"""End-to-end evaluation pipeline orchestrator.

Runs all phases: generate → answer → verify → grade → diagnose →
improve → reeval → iterate.  Manages parallelism, resumability,
and container lifecycle.

Runs on the host (conda env).  Each ``claude`` invocation is wrapped
in an Apptainer container.
"""
from __future__ import annotations

import asyncio
import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from eval.answer import run_answer_loop
from eval.container_config import (
    ContainerConfig,
    find_claude_container_path,
    make_base_container,
    make_question_container,
)
from eval.diagnose import run_diagnose
from eval.grade import GRADE_FILENAME, needs_improvement, run_grading
from eval.improve import run_improve
from eval.session import ClaudeCodeSession, MadAgentsSession
from eval.transcript import write_transcript, write_summary, write_workflow
from eval.verify import run_verification
from eval.verify.claim_db import merge_db


# ═══════════════════════════════════════════════════════════════════════
#  Config
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class PipelineConfig:
    """Pipeline configuration loaded from YAML."""

    # Questions.
    questions_mode: str = "generate"
    questions_file: str | None = None
    questions_count: int = 5
    questions_focus: str = ""
    questions_requirements: str = ""

    # Models.
    models: dict[str, str] = field(default_factory=lambda: {
        "answerer": "sonnet",
        "verifier": "sonnet",
        "diagnoser": "sonnet",
        "improver": "sonnet",
        "fact_verifier": "sonnet",
        "supervisor": "haiku",
        "extractor": "haiku",
        "triage": "haiku",
        "remember": "haiku",
        "grader": "haiku",
        "style_checker": "haiku",
        "quality_checker": "haiku",
    })

    # Parallelism.
    max_questions: int = 3
    max_api_calls: int = 5

    # Phase settings.
    answer_max_turns: int = 3
    verify_max_extract_retries: int = 3
    verify_max_verify_retries: int = 2
    improve_max_rounds: int = 10
    max_iterations: int = 3

    # Container.
    image: str = "image/pipeline/preinstall/image.sif"
    overlay_size_mb: int = 4096

    # Paths.
    docs_dir: str = "src/madagents/software_instructions/madgraph"
    docs_overview: str = "src/madagents/software_instructions/madgraph.md"
    src_dir: str = "src"
    claude_code_dir: str = "src/claude_code"
    prompts_dir: str | None = None

    @classmethod
    def from_yaml(cls, path: Path) -> "PipelineConfig":
        data = yaml.safe_load(path.read_text())
        config = cls()

        q = data.get("questions", {})
        config.questions_mode = q.get("mode", config.questions_mode)
        config.questions_file = q.get("file")
        config.questions_count = q.get("count", config.questions_count)
        config.questions_focus = q.get("focus", config.questions_focus)
        config.questions_requirements = q.get("requirements", config.questions_requirements)

        config.models.update(data.get("models", {}))

        p = data.get("parallel", {})
        config.max_questions = p.get("max_questions", config.max_questions)
        config.max_api_calls = p.get("max_api_calls", config.max_api_calls)

        a = data.get("answer", {})
        config.answer_max_turns = a.get("max_turns", config.answer_max_turns)

        v = data.get("verify", {})
        config.verify_max_extract_retries = v.get("max_extract_retries", config.verify_max_extract_retries)
        config.verify_max_verify_retries = v.get("max_verify_retries", config.verify_max_verify_retries)

        i = data.get("improve", {})
        config.improve_max_rounds = i.get("max_rounds", config.improve_max_rounds)

        it = data.get("iterate", {})
        config.max_iterations = it.get("max_iterations", config.max_iterations)

        c = data.get("container", {})
        config.image = c.get("image", config.image)
        config.overlay_size_mb = c.get("overlay_size_mb", config.overlay_size_mb)

        paths = data.get("paths", {})
        config.docs_dir = paths.get("docs", config.docs_dir)
        config.docs_overview = paths.get("docs_overview", config.docs_overview)
        config.src_dir = paths.get("src", config.src_dir)
        config.claude_code_dir = paths.get("claude_code", config.claude_code_dir)
        config.prompts_dir = paths.get("prompts_dir")

        return config


# ═══════════════════════════════════════════════════════════════════════
#  Pipeline
# ═══════════════════════════════════════════════════════════════════════

class Pipeline:
    """End-to-end evaluation pipeline.

    Usage::

        pipeline = Pipeline(config_path, repo_root, run_dir)
        await pipeline.run()
    """

    def __init__(
        self,
        config: PipelineConfig,
        repo_root: Path,
        run_dir: Path,
    ):
        self.config = config
        self.repo_root = repo_root
        self.run_dir = run_dir
        self.state = self._load_state()

        # Resolve paths relative to repo root.
        self.image = repo_root / config.image
        self.docs_dir = repo_root / config.docs_dir
        self.docs_overview = repo_root / config.docs_overview
        self.src_dir = repo_root / config.src_dir
        self.claude_code_dir = repo_root / config.claude_code_dir

        # Run directory structure.
        self.claude_config_dir = run_dir / "claude_config"
        self.docs_working_dir = run_dir / "docs_working"
        self.db_path = run_dir / "db" / "claim_db.json"
        self.log_dir = run_dir / "logs"
        self.questions_dir = run_dir / "questions"

        # Semaphore for rate limiting.
        self._sem = asyncio.Semaphore(config.max_api_calls)

        # Claude binary path (container-side).
        self._claude_bin = find_claude_container_path()

    # ── State management ──────────────────────────────────────────

    def _load_state(self) -> dict:
        state_path = self.run_dir / "state.json"
        if state_path.exists():
            return json.loads(state_path.read_text())
        return {}

    def _save_state(self, **updates):
        self.state.update(updates)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "state.json").write_text(json.dumps(self.state, indent=2))

    # ── Setup ─────────────────────────────────────────────────────

    def _setup(self):
        """Create run directory structure and copy credentials."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
        self.questions_dir.mkdir(exist_ok=True)
        self.db_path.parent.mkdir(exist_ok=True)

        # Copy credentials.
        if not self.claude_config_dir.exists():
            self.claude_config_dir.mkdir(parents=True)
            home_config = Path.home() / ".config" / ".claude"
            for fname in (".credentials.json", ".claude.json", "settings.json"):
                src = home_config / fname
                if src.is_file():
                    shutil.copy2(src, self.claude_config_dir / fname)

        # Copy docs to working dir.
        if not self.docs_working_dir.exists():
            shutil.copytree(self.docs_dir, self.docs_working_dir)
            # Include overview.
            if self.docs_overview.exists():
                shutil.copy2(
                    self.docs_overview,
                    self.docs_working_dir / "madgraph_overview.md",
                )

        # Rebuild madgraph-operator agent card from latest overview.
        self._rebuild_agent_card_from_source()

        # Save config copy.
        (self.run_dir / "config.yaml").write_text(
            yaml.dump(self.config.__dict__, default_flow_style=False)
        )

    # ── Container helpers ─────────────────────────────────────────

    def _base_container(self, claude_code_dir: Path | None = None) -> ContainerConfig:
        """Create a base container config."""
        return make_base_container(
            image=self.image,
            claude_config_dir=self.claude_config_dir,
            src_dir=self.src_dir,
            docs_dir=self.docs_working_dir,
            claude_code_dir=claude_code_dir,
        )

    def _light_container(
        self, output_dir: Path,
        extra_binds: list[tuple[str, str, str]] | None = None,
    ) -> ContainerConfig:
        """Container for cheap sessions (haiku, no overlay).

        Bind-mounts *output_dir* as ``/output``.
        """
        config = self._base_container()
        config.workdir = "/output"
        config.add_bind(output_dir, "/output")
        if extra_binds:
            for bind in extra_binds:
                config.binds.append(bind)
        return config

    def _heavy_container(
        self, output_dir: Path, overlay: Path,
        claude_code_dir: Path | None = None,
        extra_binds: list[tuple[str, str, str]] | None = None,
    ) -> ContainerConfig:
        """Container for MadAgents sessions (with overlay).

        Bind-mounts *output_dir* as ``/output``.
        """
        config = self._base_container(claude_code_dir=claude_code_dir)
        config.overlay = overlay
        config.writable_tmpfs = False
        config.workdir = "/output"
        config.add_bind(output_dir, "/output")
        if extra_binds:
            for bind in extra_binds:
                config.binds.append(bind)
        return config

    def _create_overlay(self, path: Path):
        """Create a new overlay image."""
        from eval.container_config import find_apptainer_bin
        apptainer = find_apptainer_bin()
        subprocess.run([
            apptainer, "overlay", "create",
            "--fakeroot", "--sparse",
            "--size", str(self.config.overlay_size_mb),
            str(path),
        ], check=True)

    def _ensure_overlay_dirs(self, overlay: Path):
        """Ensure bind-mount destinations exist in the overlay."""
        from eval.container_config import find_apptainer_bin
        apptainer = find_apptainer_bin()
        subprocess.run([
            apptainer, "exec", "--fakeroot",
            "--overlay", str(overlay), str(self.image),
            "bash", "-c",
            "for d in /output /workspace /madgraph_docs /src; do "
            "[ -e \"$d\" ] || mkdir -p \"$d\"; done",
        ], capture_output=True)

    # ── Session factories ─────────────────────────────────────────

    def _make_session(
        self, session_type: str, name: str,
        workdir_host: Path, container: ContainerConfig,
        transcript: list | None = None,
    ):
        """Create a session with the right type and config.

        Sets the container's ``--pwd`` to the container-side equivalent
        of *workdir_host* so Claude discovers ``.claude/`` correctly.
        """
        # Set container --pwd to mapped workdir.
        container.workdir = container.host_to_container(workdir_host)

        cls = MadAgentsSession if session_type == "madagents" else ClaudeCodeSession
        kwargs = dict(
            cwd=str(workdir_host),
            name=name,
            model=self.config.models.get(name, "sonnet"),
            permission_mode="default",
            setting_sources=["project", "local"] if session_type == "madagents" else ["local"],
            cli_path=self._claude_bin,
            transcript=transcript or [],
            log_dir=str(self.log_dir),
            container=container,
        )
        return cls(**kwargs)

    # ── Phase: Generate ───────────────────────────────────────────

    async def _generate(self) -> list[dict]:
        questions_path = self.run_dir / "questions.json"
        if questions_path.exists():
            print("Generate: skipping (questions.json exists)")
            return json.loads(questions_path.read_text())

        if self.config.questions_mode == "file" and self.config.questions_file:
            src = Path(self.config.questions_file)
            shutil.copy2(src, questions_path)
            return json.loads(questions_path.read_text())

        from eval.generate import generate_questions

        workdir = self.run_dir / "generate"
        workdir.mkdir(exist_ok=True)
        container = self._light_container(workdir)
        session = self._make_session("claude", "generator", workdir, container)

        questions = await generate_questions(
            num_questions=self.config.questions_count,
            session=session,
            output_path=workdir / "questions.json",
            focus=self.config.questions_focus,
            requirements=self.config.questions_requirements,
        )

        # Copy to run root.
        (questions_path).write_text(json.dumps(questions, indent=2))
        return questions

    # ── Phase: Per-question (answer → verify → grade → diagnose) ──

    async def _process_question(
        self, question: dict, q_idx: int,
        q_dir: Path, overlay: Path,
        iteration: str = "",
        claude_code_dir: Path | None = None,
    ):
        """Run answer → verify → grade → diagnose for one question."""
        question_text = question["text"]

        transcript = []
        answer_dir = q_dir / "answer"
        verify_dir = q_dir / "verify"
        grade_dir = q_dir / "grade"
        diagnose_dir = q_dir / "diagnose"

        # ── Answer ────────────────────────────────────────────────
        results_path = answer_dir / "results.json"
        if not results_path.exists():
            answer_dir.mkdir(parents=True, exist_ok=True)

            answerer_container = self._heavy_container(q_dir, overlay, claude_code_dir=claude_code_dir)
            answerer = self._make_session("madagents", "answerer", answer_dir, answerer_container, transcript)

            supervisor_workdir = q_dir / "session_supervisor"
            supervisor_workdir.mkdir(exist_ok=True)
            supervisor_container = self._light_container(q_dir)
            supervisor = self._make_session("claude", "supervisor", supervisor_workdir, supervisor_container, transcript)

            answer = await run_answer_loop(
                question_text=question_text,
                session=answerer,
                supervisor=supervisor,
                output_dir=answer_dir / "supervision",
                max_turns=self.config.answer_max_turns,
            )

            result = {
                "question": question_text,
                "question_index": q_idx,
                "final_response": answer.final_response,
                "final_category": answer.final_category,
                "all_messages": answerer.messages,
                "num_turns": len(answer.turns),
            }
            results_path.write_text(json.dumps(result, indent=2))
            # Write answer transcript immediately so grade/diagnose can read it.
            write_transcript(transcript, q_dir / "transcripts" / "full.json")
            write_summary(transcript, q_dir / "transcripts" / "summary.txt")
            write_workflow(transcript, q_dir / "transcripts" / "workflow")
            print(f"  q{q_idx:03d} answer: {answer.final_category}")
        else:
            print(f"  q{q_idx:03d} answer: skipped")

        # ── Verify ────────────────────────────────────────────────
        verdicts_path = verify_dir / "verdicts.json"
        if not verdicts_path.exists() or not _has_verdict_fields(verdicts_path):
            verify_dir.mkdir(parents=True, exist_ok=True)
            result_data = json.loads(results_path.read_text())
            agent_response = "\n\n".join(result_data.get("all_messages", [])) or result_data["final_response"]

            ext_wd = q_dir / "session_extractor"
            ext_wd.mkdir(exist_ok=True)
            extractor = self._make_session("claude", "extractor", ext_wd, self._light_container(q_dir), transcript)

            tri_wd = q_dir / "session_triage"
            tri_wd.mkdir(exist_ok=True)
            triage = self._make_session("claude", "triage", tri_wd, self._light_container(q_dir), transcript)

            ver_container = self._heavy_container(q_dir, overlay)
            verifier = self._make_session("madagents", "verifier", verify_dir, ver_container, transcript)

            rem_wd = q_dir / "session_remember"
            rem_wd.mkdir(exist_ok=True)
            remember = self._make_session("claude", "remember", rem_wd, self._light_container(q_dir), transcript)

            claims, verdicts = await run_verification(
                question_text=question_text,
                agent_response=agent_response,
                extractor_session=extractor,
                triage_session=triage,
                verifier_session=verifier,
                remember_session=remember,
                output_dir=verify_dir,
                db_path=self.db_path,
            )

            n_correct = sum(1 for v in verdicts if v.get("correct") is True)
            n_incorrect = sum(1 for v in verdicts if v.get("correct") is False)
            print(f"  q{q_idx:03d} verify: {n_correct} correct, {n_incorrect} incorrect")
        else:
            print(f"  q{q_idx:03d} verify: skipped")

        # ── Grade ─────────────────────────────────────────────────
        grade_path = grade_dir / GRADE_FILENAME
        # Prefer the cleaned answerer workflow; fall back to full transcript.
        workflow_dir = answer_dir / "transcripts" / "workflow"
        transcript_path = workflow_dir / "answerer.json"
        if not transcript_path.exists():
            transcript_path = answer_dir / "transcripts" / "full.json"
        if not grade_path.exists():
            grade_dir.mkdir(parents=True, exist_ok=True)
            verdicts = json.loads(verdicts_path.read_text())

            grd_wd = q_dir / "session_grader"
            grd_wd.mkdir(exist_ok=True)
            grader = self._make_session("claude", "grader", grd_wd, self._light_container(q_dir), transcript)

            grade = await run_grading(
                question_text=question_text,
                verdicts=verdicts,
                session=grader,
                verdicts_path=verdicts_path,
                output_path=grade_path,
                transcript_path=transcript_path,
            )
            tags = grade.get("tags", [])
            tags_str = f" [{', '.join(tags)}]" if tags else ""
            print(f"  q{q_idx:03d} grade: {grade.get('grade', '?')}{tags_str}")
        else:
            grade = json.loads(grade_path.read_text()) if grade_path.exists() else {}
            print(f"  q{q_idx:03d} grade: skipped")

        # ── Diagnose ──────────────────────────────────────────────
        diagnose_path = diagnose_dir / "diagnoses.json"
        should_diagnose = needs_improvement(grade)

        if should_diagnose and not diagnose_path.exists():
            diagnose_dir.mkdir(parents=True, exist_ok=True)

            diag_wd = q_dir / "session_diagnoser"
            diag_wd.mkdir(exist_ok=True)
            diagnoser = self._make_session("claude", "diagnoser", diag_wd, self._light_container(q_dir), transcript)

            await run_diagnose(
                question_text=question_text,
                session=diagnoser,
                verdicts_path=verdicts_path,
                transcript_path=transcript_path,
                output_path=diagnose_path,
                grade=grade,
            )
            diagnoses = json.loads(diagnose_path.read_text())
            total = sum(len(v) for v in diagnoses.values())
            print(f"  q{q_idx:03d} diagnose: {total} findings")
        elif not diagnose_path.exists():
            # Clean CORRECT — write empty diagnoses.
            diagnose_dir.mkdir(parents=True, exist_ok=True)
            diagnose_path.write_text('{"doc_gap": [], "doc_incorrect": [], "doc_ambiguous": []}')
            print(f"  q{q_idx:03d} diagnose: skipped (clean CORRECT)")
        else:
            print(f"  q{q_idx:03d} diagnose: skipped")

        # Save full transcript (all phases). Skip if empty (resumed run).
        if transcript:
            write_transcript(transcript, q_dir / "transcripts" / "full.json")
            write_summary(transcript, q_dir / "transcripts" / "summary.txt")
            write_workflow(transcript, q_dir / "transcripts" / "workflow")

    async def _run_questions(
        self, questions: list[dict], phase_dir: Path,
        phases: list[str] | None = None,
    ):
        """Run per-question processing in parallel."""
        sem = asyncio.Semaphore(self.config.max_questions)

        async def _process_one(q, idx):
            async with sem:
                q_dir = phase_dir / f"q{idx:03d}"
                q_dir.mkdir(parents=True, exist_ok=True)

                overlay = q_dir / "overlay.img"
                if not overlay.exists():
                    self._create_overlay(overlay)
                    self._ensure_overlay_dirs(overlay)

                await self._process_question(q, idx, q_dir, overlay)

        tasks = [
            asyncio.create_task(_process_one(q, i))
            for i, q in enumerate(questions)
        ]
        await asyncio.gather(*tasks)

    # ── Phase: Improve ────────────────────────────────────────────

    async def _improve(
        self, iteration: int, questions: list[dict],
        improver_session=None,
    ) -> dict:
        """Merge all diagnoses and improve docs.

        Args:
            iteration: Iteration number (0 for initial improve).
            questions: All questions.
            improver_session: Reusable improver session.  When provided
                the session is reused across iterations so the improver
                retains context about what it already tried.
        """
        improve_dir = self.run_dir / f"improve_{iteration}"
        summary_path = improve_dir / "improve_summary.json"

        if summary_path.exists():
            print(f"Improve {iteration}: skipped")
            return json.loads(summary_path.read_text())

        # Collect all diagnoses.
        if iteration == 0:
            phase_dir = self.questions_dir
        else:
            phase_dir = self.run_dir / f"iter_{iteration}" / "diagnose"

        all_diagnoses = {"doc_gap": [], "doc_incorrect": [], "doc_ambiguous": []}
        for i, q in enumerate(questions):
            diag_path = phase_dir / f"q{i:03d}" / "diagnose" / "diagnoses.json"
            if not diag_path.exists():
                # Try alternate path for iteration dirs.
                diag_path = phase_dir / f"q{i:03d}" / "diagnoses.json"
            if diag_path.exists():
                d = json.loads(diag_path.read_text())
                for cat in all_diagnoses:
                    all_diagnoses[cat].extend(d.get(cat, []))

        total = sum(len(v) for v in all_diagnoses.values())
        if total == 0:
            print(f"Improve {iteration}: no findings")
            summary = {"approved": True, "rounds": [], "final_changes": []}
            improve_dir.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(json.dumps(summary, indent=2))
            return summary

        # Write merged diagnoses.
        improve_dir.mkdir(parents=True, exist_ok=True)
        merged_path = improve_dir / "diagnoses_merged.json"
        merged_path.write_text(json.dumps(all_diagnoses, indent=2))
        print(f"Improve {iteration}: {total} findings from {len(questions)} questions")

        # Collect reference answers for the improver (inline, never written
        # to disk — answerers must not see them during re-evaluation).
        ref_answers = [
            {"question": q["text"], "reference_answer": q.get("reference_answer", "")}
            for q in questions if q.get("reference_answer")
        ] or None

        # Collect initial claims from all verifications.
        initial_claims = []
        for i in range(len(questions)):
            vp = self.questions_dir / f"q{i:03d}" / "verify" / "verdicts.json"
            if vp.exists():
                vs = json.loads(vp.read_text())
                initial_claims.extend(v for v in vs if v.get("correct") is not None)

        # Use an overlay from the first question (MadGraph installed).
        overlay = self._find_any_overlay()

        transcript = []

        # All improve sessions bind-mount improve_dir as /output
        # and docs_working as /docs_working.
        docs_bind = (str(self.docs_working_dir), "/docs_working", "rw")

        # Reuse the improver session across iterations so it retains
        # context about what it already tried.  Checker sessions are
        # created fresh — they evaluate current state without history.
        if improver_session is None:
            improver_wd = improve_dir / "session_improver"
            improver_wd.mkdir(exist_ok=True)
            improver_session = self._make_session("claude", "improver", improver_wd,
                self._light_container(improve_dir, extra_binds=[docs_bind]), transcript)

        fact_wd = improve_dir / "session_fact_verifier"
        fact_wd.mkdir(exist_ok=True)
        if overlay:
            fact_container = self._heavy_container(improve_dir, overlay, extra_binds=[docs_bind])
        else:
            fact_container = self._light_container(improve_dir, extra_binds=[docs_bind])
        fact_verifier = self._make_session("madagents" if overlay else "claude", "fact_verifier", fact_wd, fact_container, transcript)

        style_wd = improve_dir / "session_style"
        style_wd.mkdir(exist_ok=True)
        style = self._make_session("claude", "style_checker", style_wd,
            self._light_container(improve_dir, extra_binds=[docs_bind]), transcript)

        quality_wd = improve_dir / "session_quality"
        quality_wd.mkdir(exist_ok=True)
        quality = self._make_session("claude", "quality_checker", quality_wd,
            self._light_container(improve_dir, extra_binds=[docs_bind]), transcript)

        docs_working_copy = improve_dir / "docs_working"

        summary = await run_improve(
            diagnoses_path=merged_path,
            docs_source_dir=self.docs_working_dir,
            docs_working_dir=docs_working_copy,
            output_dir=improve_dir,
            improver_session=improver_session,
            fact_verifier_session=fact_verifier,
            style_session=style,
            quality_session=quality,
            initial_claims=initial_claims,
            db_path=self.db_path,
            max_rounds=self.config.improve_max_rounds,
            reference_answers=ref_answers,
        )

        # If approved, update docs_working.
        if summary.get("approved") or summary.get("final_changes"):
            if docs_working_copy.exists():
                # Update the main docs_working.
                for item in self.docs_working_dir.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                shutil.copytree(docs_working_copy, self.docs_working_dir, dirs_exist_ok=True)
                print(f"  Updated docs_working/")

        # Merge staging.
        staging = improve_dir / "staging"
        if staging.is_dir():
            merge_db(self.db_path, staging)

        return summary

    def _find_any_overlay(self) -> Path | None:
        """Find any existing overlay (with MadGraph installed)."""
        for q_dir in sorted(self.questions_dir.glob("q*")):
            overlay = q_dir / "overlay.img"
            if overlay.exists():
                return overlay
        return None

    # ── Phase: Get failed questions ───────────────────────────────

    def _get_failed_questions(
        self, questions: list[dict], phase_dir: Path,
    ) -> list[tuple[int, dict]]:
        """Return questions that are not graded clean CORRECT."""
        failed = []
        for i, q in enumerate(questions):
            grade_path = phase_dir / f"q{i:03d}" / "grade" / GRADE_FILENAME
            if grade_path.exists():
                grade = json.loads(grade_path.read_text())
                has_problems = needs_improvement(grade)
                if has_problems:
                    failed.append((i, q))
            else:
                failed.append((i, q))
        return failed

    # ── Rebuild agent card ────────────────────────────────────────

    def _rebuild_agent_card_from_source(self) -> None:
        """Rebuild the madgraph-operator agent card in src/claude_code from the source overview.

        Called once at setup to ensure the agent card reflects the latest overview.
        """
        header = self.repo_root / "claude_code" / "prompts" / "madgraph-operator.header.md"
        overview = self.repo_root / "src" / "madagents" / "software_instructions" / "madgraph.md"
        output = self.claude_code_dir / ".claude" / "agents" / "madgraph-operator.md"

        if not header.exists() or not overview.exists():
            return

        header_text = header.read_text().rstrip("\n") + "\n"
        overview_text = overview.read_text()
        shifted = re.sub(r"^(#+)", r"#\1", overview_text, flags=re.MULTILINE)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(header_text + "\n" + shifted)

    def _rebuild_agent_card(self) -> Path | None:
        """Rebuild madgraph-operator agent card with current docs overview.

        Returns path to a local claude_code copy, or None if no rebuild needed.
        """
        header = self.repo_root / "claude_code" / "prompts" / "madgraph-operator.header.md"
        overview = self.docs_working_dir / "madgraph_overview.md"

        if not header.exists() or not overview.exists():
            return None

        local_cc = self.run_dir / "claude_code_local"
        if local_cc.exists():
            shutil.rmtree(local_cc)
        shutil.copytree(self.claude_code_dir, local_cc)

        header_text = header.read_text().rstrip("\n") + "\n"
        overview_text = overview.read_text()
        shifted = re.sub(r"^(#+)", r"#\\1", overview_text, flags=re.MULTILINE)
        (local_cc / ".claude" / "agents" / "madgraph-operator.md").write_text(
            header_text + "\n" + shifted
        )

        return local_cc

    # ── Main run ──────────────────────────────────────────────────

    async def run(self):
        """Run the full pipeline."""
        print(f"\n{'=' * 60}")
        print(f"  Pipeline: {self.run_dir}")
        print(f"{'=' * 60}\n")

        self._setup()

        # ── Generate ──────────────────────────────────────────────
        print("─── Generate ───")
        questions = await self._generate()
        print(f"  {len(questions)} questions\n")
        self._save_state(phase="generate", n_questions=len(questions))

        # ── Per-question: answer → verify → grade → diagnose ─────
        print("─── Per-question: answer → verify → grade → diagnose ───")
        await self._run_questions(questions, self.questions_dir)
        self._save_state(phase="per_question")

        # ── Create persistent improver session ─────────────────────
        # The improver is reused across iterations so it retains
        # context about what it already tried.
        docs_bind = (str(self.docs_working_dir), "/docs_working", "rw")
        improver_wd = self.run_dir / "session_improver"
        improver_wd.mkdir(exist_ok=True)
        improver_session = self._make_session(
            "claude", "improver", improver_wd,
            self._light_container(self.run_dir, extra_binds=[docs_bind]),
        )

        # ── Improve ───────────────────────────────────────────────
        print("\n─── Improve ───")
        await self._improve(0, questions, improver_session=improver_session)
        self._save_state(phase="improve_0")

        # ── Iterate ───────────────────────────────────────────────
        converged: set[int] = set()  # question indices that reached CORRECT

        for iteration in range(1, self.config.max_iterations + 1):
            # Determine which questions failed. Check the latest results
            # for each question, but skip any that already converged.
            if iteration == 1:
                failed = self._get_failed_questions(questions, self.questions_dir)
            else:
                # Only check questions that were re-evaluated last iteration.
                prev_reeval = self.run_dir / f"iter_{iteration - 1}" / "reeval"
                failed = []
                for idx, q in enumerate(questions):
                    if idx in converged:
                        continue
                    grade_path = prev_reeval / f"q{idx:03d}" / "grade" / GRADE_FILENAME
                    if grade_path.exists():
                        grade = json.loads(grade_path.read_text())
                        needs_work = needs_improvement(grade)
                        is_clean = not needs_work
                        if is_clean:
                            converged.add(idx)
                            continue
                        failed.append((idx, q))
                    else:
                        # Wasn't re-evaluated last iteration — check original.
                        failed.append((idx, q))

            # Remove any newly converged from failed.
            failed = [(idx, q) for idx, q in failed if idx not in converged]

            if not failed:
                print(f"\n  All questions CORRECT — done!")
                break

            print(f"\n─── Iteration {iteration} ({len(failed)} failed questions) ───")

            iter_dir = self.run_dir / f"iter_{iteration}"

            # Rebuild agent card with updated docs.
            local_cc = self._rebuild_agent_card()

            # Reeval failed questions.
            print("  Reeval:")
            reeval_dir = iter_dir / "reeval"
            sem = asyncio.Semaphore(self.config.max_questions)

            async def _reeval_one(idx, q):
                async with sem:
                    q_dir = reeval_dir / f"q{idx:03d}"
                    q_dir.mkdir(parents=True, exist_ok=True)
                    # Copy overlay from original question.
                    src_overlay = self.questions_dir / f"q{idx:03d}" / "overlay.img"
                    dst_overlay = q_dir / "overlay.img"
                    if not dst_overlay.exists() and src_overlay.exists():
                        shutil.copy2(src_overlay, dst_overlay)
                        self._ensure_overlay_dirs(dst_overlay)
                    elif not dst_overlay.exists():
                        self._create_overlay(dst_overlay)
                        self._ensure_overlay_dirs(dst_overlay)
                    await self._process_question(q, idx, q_dir, dst_overlay, claude_code_dir=local_cc)

            tasks = [asyncio.create_task(_reeval_one(idx, q)) for idx, q in failed]
            await asyncio.gather(*tasks)

            # Check which of the re-evaluated questions still need work.
            still_failed = []
            for idx, q in failed:
                grade_path = reeval_dir / f"q{idx:03d}" / "grade" / GRADE_FILENAME
                if grade_path.exists():
                    grade = json.loads(grade_path.read_text())
                    has_problems = needs_improvement(grade)
                    if has_problems:
                        still_failed.append((idx, q))
                else:
                    still_failed.append((idx, q))
            if not still_failed:
                print(f"  All questions CORRECT after iteration {iteration}!")
                break

            # Diagnose still-failing.
            print(f"  Diagnose ({len(still_failed)} questions):")
            diag_dir = iter_dir / "diagnose"
            for idx, q in still_failed:
                q_diag_dir = diag_dir / f"q{idx:03d}"
                q_diag_dir.mkdir(parents=True, exist_ok=True)
                # Re-diagnose using reeval verdicts.
                verdicts_path = reeval_dir / f"q{idx:03d}" / "verify" / "verdicts.json"
                transcript_path = reeval_dir / f"q{idx:03d}" / "answer" / "transcripts" / "workflow" / "answerer.json"
                if not transcript_path.exists():
                    transcript_path = reeval_dir / f"q{idx:03d}" / "answer" / "transcripts" / "full.json"
                diagnose_path = q_diag_dir / "diagnoses.json"
                grade_path = reeval_dir / f"q{idx:03d}" / "grade" / GRADE_FILENAME
                reeval_grade = json.loads(grade_path.read_text()) if grade_path.exists() else None

                if not diagnose_path.exists():
                    diag_wd = q_diag_dir / "session_diagnoser"
                    diag_wd.mkdir(exist_ok=True)
                    # Mount the reeval question dir so diagnoser can read verdicts/transcripts.
                    reeval_q_dir = reeval_dir / f"q{idx:03d}"
                    diagnoser = self._make_session("claude", "diagnoser", diag_wd,
                        self._light_container(q_diag_dir, extra_binds=[
                            (str(reeval_q_dir), "/reeval", "ro"),
                        ]))
                    await run_diagnose(
                        question_text=q["text"],
                        session=diagnoser,
                        verdicts_path=verdicts_path,
                        transcript_path=transcript_path,
                        output_path=diagnose_path,
                        grade=reeval_grade,
                    )

            # Improve with new diagnoses (reuses the same improver session).
            print(f"  Improve:")
            await self._improve(iteration, questions, improver_session=improver_session)

            self._save_state(phase=f"iter_{iteration}")

        else:
            n_converged = len(converged)
            n_total = len(questions)
            print(f"\n  Max iterations ({self.config.max_iterations}) reached. "
                  f"{n_converged}/{n_total} questions converged.")

        # ── Merge claim DB staging ────────────────────────────────
        for staging in self.run_dir.rglob("staging"):
            if staging.is_dir() and list(staging.glob("*.json")):
                merge_db(self.db_path, staging)

        # ── Final summary ─────────────────────────────────────────
        self._save_state(phase="completed")
        print(f"\n{'=' * 60}")
        print(f"  Pipeline completed: {self.run_dir}")
        print(f"  Docs: {self.docs_working_dir}")
        print(f"{'=' * 60}\n")


# ═══════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════

def _has_verdict_fields(path: Path) -> bool:
    """Check if a verdicts file has verdict fields (not just claims)."""
    try:
        data = json.loads(path.read_text())
        return isinstance(data, list) and len(data) > 0 and "correct" in data[0]
    except Exception:
        return False
