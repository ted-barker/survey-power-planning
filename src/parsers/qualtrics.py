#!/usr/bin/env python3
"""
Qualtrics QSF file parser.

Extracts survey structure, questions, loops, skip logic, and metadata
from Qualtrics QSF (JSON) format.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Question:
    """Represents a single survey question."""

    id: str
    text: str
    type: str  # SingleAnswer, MultipleAnswer, Matrix, TE (text entry), etc.
    position: int

    # Question properties
    choices: List[str] = field(default_factory=list)
    sub_questions: List[str] = field(default_factory=list)  # For matrix rows

    # Metadata
    is_required: bool = False
    randomize_choices: bool = False
    validation_type: Optional[str] = None

    # Matrix-specific
    rows: int = 0
    columns: int = 0

    # Loop context
    in_loop: bool = False
    loop_id: Optional[str] = None
    loop_iteration: Optional[int] = None

    # Skip logic
    has_display_logic: bool = False
    display_logic_condition: Optional[str] = None

    def __repr__(self) -> str:
        return f"Question(id={self.id}, type={self.type}, position={self.position}, text={self.text[:50]}...)"


@dataclass
class Loop:
    """Represents a looped question block."""

    id: str
    name: str
    iterations: int
    question_ids: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Loop(id={self.id}, iterations={self.iterations}, questions={len(self.question_ids)})"


@dataclass
class SkipLogic:
    """Represents skip logic / branching."""

    question_id: str
    condition: str
    target: str  # Next question ID or "EndOfSurvey"

    def __repr__(self) -> str:
        return f"SkipLogic(from={self.question_id}, condition={self.condition[:30]}...)"


@dataclass
class BlockRandomizer:
    """Represents block randomization (BIBD)."""

    id: str
    subset: int  # Number of blocks respondent sees
    total_blocks: int  # Total blocks available
    block_ids: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"BlockRandomizer(subset={self.subset}/{self.total_blocks})"


@dataclass
class Survey:
    """Represents the complete survey structure."""

    name: str
    questions: List[Question] = field(default_factory=list)
    loops: List[Loop] = field(default_factory=list)
    skip_logic: List[SkipLogic] = field(default_factory=list)
    block_randomizers: List[BlockRandomizer] = field(default_factory=list)

    # Metadata
    intro_text: str = ""
    outro_text: str = ""
    estimated_time: Optional[int] = None  # Minutes
    uses_bibd: bool = False  # Balanced Incomplete Block Design
    effective_questions: Optional[int] = None  # Questions per respondent (if BIBD)

    # Skip logic metadata
    questions_with_display_logic: int = 0
    skip_logic_intensity: float = 0.0  # 0.0-1.0 (% of questions with conditions)

    def __repr__(self) -> str:
        return (f"Survey(name={self.name}, "
                f"questions={len(self.questions)}, "
                f"loops={len(self.loops)}, "
                f"skip_logic={len(self.skip_logic)})")

    def get_question(self, question_id: str) -> Optional[Question]:
        """Get question by ID."""
        for q in self.questions:
            if q.id == question_id:
                return q
        return None

    def get_questions_by_type(self, qtype: str) -> List[Question]:
        """Get all questions of a specific type."""
        return [q for q in self.questions if q.type == qtype]

    def get_questions_in_loop(self, loop_id: str) -> List[Question]:
        """Get all questions in a specific loop."""
        return [q for q in self.questions if q.loop_id == loop_id]


class QualtricsParser:
    """Parse Qualtrics QSF files into Survey objects."""

    # Map Qualtrics question types to our types
    TYPE_MAPPING = {
        "MC": "SingleAnswer",  # Multiple choice (single answer)
        "MA": "MultipleAnswer",  # Multiple answer
        "Matrix": "Matrix",
        "TE": "TextEntry",
        "DB": "DescriptiveText",  # Description block
        "Timing": "Timing",
        "Slider": "Slider",
        "RO": "RankOrder",
        "CS": "ConstantSum",
        "PGR": "ProfileGrid",
        "SBS": "SideBySide",
    }

    def parse_file(self, qsf_path: Path) -> Survey:
        """
        Parse a QSF file and return Survey object.

        Args:
            qsf_path: Path to .qsf file

        Returns:
            Survey object with all questions, loops, and skip logic
        """
        with open(qsf_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return self.parse_json(data)

    def parse_json(self, data: Dict[str, Any]) -> Survey:
        """Parse QSF JSON data into Survey object."""

        # Extract survey metadata
        survey_elements = data.get("SurveyElements", [])

        survey = Survey(name=self._extract_survey_name(data))

        # First pass: extract questions
        position = 0
        for element in survey_elements:
            element_type = element.get("Element")

            if element_type == "SQ":  # Survey Question
                question = self._parse_question(element, position)
                if question:
                    survey.questions.append(question)
                    position += 1

            elif element_type == "BL":  # Block (may contain loops)
                block_questions = self._parse_block(element, position)
                survey.questions.extend(block_questions)
                position += len(block_questions)

            elif element_type == "FL":  # Flow (skip logic, loops, randomizers)
                loops, skip_logic, block_randomizers = self._parse_flow(element)
                survey.loops.extend(loops)
                survey.skip_logic.extend(skip_logic)
                survey.block_randomizers.extend(block_randomizers)

        # Second pass: attach loop metadata to questions
        self._attach_loop_metadata(survey)

        # Calculate effective questions if BIBD detected
        self._calculate_effective_questions(survey)

        # Analyze skip/display logic
        self._analyze_skip_logic(survey)

        return survey

    def _extract_survey_name(self, data: Dict[str, Any]) -> str:
        """Extract survey name from QSF."""
        for element in data.get("SurveyElements", []):
            if element.get("Element") == "SurveyInfo":
                return element.get("Payload", {}).get("SurveyName", "Untitled Survey")
        return "Untitled Survey"

    def _parse_question(self, element: Dict[str, Any], position: int) -> Optional[Question]:
        """Parse a single question element."""
        payload = element.get("Payload", {})

        qid = payload.get("QuestionID")
        if not qid:
            return None

        # Extract question text (strip HTML)
        qtext = payload.get("QuestionText", "")
        qtext = self._strip_html(qtext)

        # Question type
        selector = payload.get("Selector", "")
        qtype = payload.get("QuestionType", "")
        mapped_type = self.TYPE_MAPPING.get(qtype, qtype)

        # Qualtrics encodes "check-all-that-apply" as QuestionType=MC with
        # Selector=MAVR (multi-answer vertical) or MAHR (multi-answer horizontal).
        # Treat these as MultipleAnswer rather than SingleAnswer.
        if qtype == "MC" and selector in ("MAVR", "MAHR"):
            mapped_type = "MultipleAnswer"

        # Text entry: distinguish short (single-line) from long-form (multi-line/essay).
        # Selector=SL=single line (short), ML=multi line, ESTB=essay text box,
        # FORM=multi-field form. ML/ESTB/FORM = long open-ended → much higher load.
        if qtype == "TE" and selector in ("ML", "ESTB", "FORM"):
            mapped_type = "TextEntryLong"

        # Choices
        choices = []
        choice_order = payload.get("Choices", {})
        if isinstance(choice_order, dict):
            for choice_id, choice_data in choice_order.items():
                if isinstance(choice_data, dict):
                    choice_text = choice_data.get("Display", "")
                    choices.append(self._strip_html(choice_text))

        # Matrix rows and columns
        rows = 0
        columns = 0
        sub_questions = []

        if mapped_type == "Matrix":
            # Rows (sub-questions)
            answers = payload.get("Answers", {})
            if isinstance(answers, dict):
                rows = len(answers)
                for ans_id, ans_data in answers.items():
                    if isinstance(ans_data, dict):
                        sub_text = ans_data.get("Display", "")
                        sub_questions.append(self._strip_html(sub_text))

            # Columns (choices)
            columns = len(choices)

        # Validation and randomization
        is_required = payload.get("Validation", {}).get("Settings", {}).get("ForceResponse", "OFF") == "ON"
        randomize = payload.get("Configuration", {}).get("QuestionDescriptionOption") == "UseText"

        # Check for DisplayLogic (skip logic)
        has_display_logic = False
        display_logic_condition = None
        display_logic = payload.get("DisplayLogic")
        if display_logic:
            has_display_logic = True
            # Simplified extraction - just note that logic exists
            # Full parsing would require recursive logic tree analysis
            if isinstance(display_logic, dict):
                display_logic_condition = str(display_logic)[:100]  # Truncate for storage

        question = Question(
            id=qid,
            text=qtext,
            type=mapped_type,
            position=position,
            choices=choices,
            sub_questions=sub_questions,
            is_required=is_required,
            randomize_choices=randomize,
            rows=rows,
            columns=columns,
            has_display_logic=has_display_logic,
            display_logic_condition=display_logic_condition,
        )

        return question

    def _parse_block(self, element: Dict[str, Any], start_position: int) -> List[Question]:
        """Parse a block element (may contain multiple questions)."""
        # Simplified: blocks usually just group questions
        # Real implementation would extract questions from block
        return []

    def _parse_flow(self, element: Dict[str, Any]) -> tuple[List[Loop], List[SkipLogic], List[BlockRandomizer]]:
        """Parse flow element to extract loops, skip logic, and block randomizers."""
        loops = []
        skip_logic = []
        block_randomizers = []

        payload = element.get("Payload", {})
        flow_items = payload.get("Flow", [])

        for item in flow_items:
            flow_type = item.get("Type")

            if flow_type == "LoopAndMerge":
                # Extract loop
                loop = self._parse_loop(item)
                if loop:
                    loops.append(loop)

            elif flow_type == "Branch":
                # Extract skip logic
                logic = self._parse_branch(item)
                if logic:
                    skip_logic.extend(logic)

            elif flow_type == "BlockRandomizer":
                # Extract block randomization (BIBD)
                randomizer = self._parse_block_randomizer(item)
                if randomizer:
                    block_randomizers.append(randomizer)

        return loops, skip_logic, block_randomizers

    def _parse_loop(self, item: Dict[str, Any]) -> Optional[Loop]:
        """Parse a loop item."""
        loop_id = item.get("ID")
        loop_name = item.get("Description", "Unnamed Loop")

        # Extract iteration count (may be dynamic in QSF)
        # For now, assume fixed count or default to 3
        iterations = 3  # Placeholder - need to inspect actual QSF structure

        # Extract question IDs in loop
        question_ids = []
        # TODO: Extract from flow structure

        return Loop(
            id=loop_id,
            name=loop_name,
            iterations=iterations,
            question_ids=question_ids
        )

    def _parse_branch(self, item: Dict[str, Any]) -> List[SkipLogic]:
        """Parse skip logic / branching."""
        skip_logic = []

        # Extract condition and target
        condition = item.get("Condition", "")
        target = item.get("Target", "")

        # TODO: Parse actual branching logic from QSF structure

        return skip_logic

    def _parse_block_randomizer(self, item: Dict[str, Any]) -> Optional[BlockRandomizer]:
        """Parse block randomizer (BIBD)."""
        randomizer_id = item.get("FlowID", "")
        subset = item.get("SubSet")

        # Get blocks in randomizer
        flow_items = item.get("Flow", [])
        block_ids = []

        for flow_item in flow_items:
            item_type = flow_item.get("Type")

            if item_type == "Group":
                # Groups contain blocks - use the Group's FlowID
                group_id = flow_item.get("FlowID")
                if group_id:
                    block_ids.append(group_id)

            elif item_type == "Block":
                # Direct block reference
                block_id = flow_item.get("ID")
                if block_id:
                    block_ids.append(block_id)

        if subset and block_ids:
            try:
                subset_int = int(subset)
                return BlockRandomizer(
                    id=randomizer_id,
                    subset=subset_int,
                    total_blocks=len(block_ids),
                    block_ids=block_ids
                )
            except (ValueError, TypeError):
                pass

        return None

    def _attach_loop_metadata(self, survey: Survey) -> None:
        """Attach loop metadata to questions."""
        for loop in survey.loops:
            for qid in loop.question_ids:
                question = survey.get_question(qid)
                if question:
                    question.in_loop = True
                    question.loop_id = loop.id

    def _calculate_effective_questions(self, survey: Survey) -> None:
        """Calculate effective questions per respondent if BIBD detected."""
        if not survey.block_randomizers:
            return

        # Check if we have BIBD (subset < total blocks)
        for randomizer in survey.block_randomizers:
            if randomizer.subset < randomizer.total_blocks:
                survey.uses_bibd = True

                # Estimate: questions per block × subset + questions outside randomizer
                # For now, simple heuristic: total_questions × (subset / total_blocks)
                reduction_ratio = randomizer.subset / randomizer.total_blocks
                survey.effective_questions = int(len(survey.questions) * reduction_ratio)

                # Add back any questions outside the randomizer (intro/demo questions)
                # This is an approximation - actual count depends on flow structure
                estimated_non_randomized = min(5, len(survey.questions) - survey.effective_questions)
                survey.effective_questions += estimated_non_randomized

                break  # Only handle first randomizer for now

    def _analyze_skip_logic(self, survey: Survey) -> None:
        """Analyze DisplayLogic to estimate skip logic impact."""
        questions_with_logic = 0

        # Count questions with DisplayLogic
        for question in survey.questions:
            if question.has_display_logic:
                questions_with_logic += 1

        if len(survey.questions) > 0:
            survey.questions_with_display_logic = questions_with_logic
            survey.skip_logic_intensity = questions_with_logic / len(survey.questions)

    @staticmethod
    def _strip_html(text: str) -> str:
        """Strip HTML tags from text."""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()


def load_qsf(file_path: str) -> Survey:
    """
    Convenience function to load a QSF file.

    Args:
        file_path: Path to .qsf file

    Returns:
        Survey object

    Example:
        >>> survey = load_qsf('data/sample-surveys/user-research.qsf')
        >>> print(f"Survey has {len(survey.questions)} questions")
    """
    parser = QualtricsParser()
    return parser.parse_file(Path(file_path))
