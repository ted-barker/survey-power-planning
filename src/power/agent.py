"""
Conversational agent for guided power analysis

Helps researchers select appropriate tests and parameters through Q&A
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import re


@dataclass
class ConversationState:
    """Track state of conversation with researcher"""
    workflow: Optional[str] = None  # 'stats_first', 'survey_first', or None
    research_question: Optional[str] = None
    study_type: Optional[str] = None  # 'comparative', 'predictive', 'descriptive'
    test_type: Optional[str] = None
    n_groups: Optional[int] = None
    n_predictors: Optional[int] = None
    segments: Optional[Dict] = None
    effect_size: Optional[float] = None
    alpha: float = 0.05
    power: float = 0.80
    has_existing_n: bool = False
    existing_n: Optional[int] = None
    has_survey: bool = False
    fatigue_score: Optional[float] = None  # Stores dropoff_rate now
    ctr: Optional[float] = None
    recommendations: List[str] = field(default_factory=list)
    history: List[Tuple[str, str]] = field(default_factory=list)


class PowerAnalysisAgent:
    """
    Conversational agent for guided power analysis.

    Workflow:
    1. Ask about research question
    2. Determine appropriate test type
    3. Guide parameter selection (effect size, groups, etc.)
    4. Run power analysis
    5. Integrate with fatigue audit if survey available
    6. Provide recommendations
    """

    def __init__(self):
        self.state = ConversationState()
        self.current_step = 'start'

    def start_conversation(self) -> str:
        """Begin conversation with researcher."""
        self.current_step = 'workflow_choice'
        return (
            "Hi! I'll help you plan your sample size for your survey research.\n\n"
            "**Choose your workflow:**\n\n"
            "**1. Design study → Calculate sample**\n"
            "   → I know my research question/test\n"
            "   → Calculate: sample size needed → invitations to send\n\n"
            "**2. Survey constraints → Test feasibility**\n"
            "   → I have fixed invitations/budget\n"
            "   → Calculate: sample I'll get → what tests are feasible\n\n"
            "**3. Just statistical power** (quick)\n"
            "   → How many sample for my test?\n"
            "   → No survey planning\n\n"
            "Type '1', '2', or '3'\n\n"
            "*Tip: Type 'restart' to start over, 'back' to go to previous step*"
        )

    def process_response(self, user_input: str) -> str:
        """
        Process user response and determine next question.

        Args:
            user_input: User's response to previous question

        Returns:
            Next question or analysis result
        """
        # Check for restart command
        if user_input.lower().strip() in ['restart', 'start over', 'reset']:
            self.__init__()  # Reset state
            return self.start_conversation()

        # Check for back command
        if user_input.lower().strip() in ['back', 'undo', 'previous']:
            return self._handle_back()

        # Store in history
        self.state.history.append((self.current_step, user_input))

        # Route based on current step
        if self.current_step == 'workflow_choice':
            return self._handle_workflow_choice(user_input)
        elif self.current_step == 'survey_constraints':
            return self._handle_survey_constraints(user_input)
        elif self.current_step == 'ctr_reverse':
            return self._handle_ctr_reverse(user_input)
        elif self.current_step == 'dropoff_reverse':
            return self._handle_dropoff_reverse(user_input)
        elif self.current_step == 'research_question':
            return self._handle_research_question(user_input)
        elif self.current_step == 'study_type_confirmation':
            return self._handle_study_type_confirmation(user_input)
        elif self.current_step == 'test_details':
            return self._handle_test_details(user_input)
        elif self.current_step == 'effect_size':
            return self._handle_effect_size(user_input)
        elif self.current_step == 'existing_n':
            return self._handle_existing_n(user_input)
        elif self.current_step == 'survey_availability':
            return self._handle_survey_availability(user_input)
        elif self.current_step == 'fatigue_score':
            return self._handle_fatigue_score(user_input)
        elif self.current_step == 'fatigue_score_first':
            return self._handle_fatigue_score_first(user_input)
        elif self.current_step == 'ctr':
            return self._handle_ctr(user_input)
        else:
            return "I'm not sure what to ask next. Let's start over."

    def _handle_fatigue_score_first(self, user_input: str) -> str:
        """Handle fatigue score when collected FIRST (workflow 2)."""
        # Try to parse number
        match = re.search(r'(\d+(?:\.\d+)?)', user_input)
        if match:
            self.state.fatigue_score = float(match.group())

            # Now ask about research question for power analysis
            self.current_step = 'research_question'
            return (
                f"Got it! Fatigue score: {self.state.fatigue_score:.0f}/100\n\n"
                f"Now let's figure out how many participants you need.\n\n"
                f"What are you trying to find out with your survey?\n"
                f"For example:\n"
                f"- 'Do users prefer Design A or Design B?'\n"
                f"- 'What predicts customer satisfaction?'\n"
                f"- 'Are there differences across user segments?'"
            )
        else:
            return "Please enter the fatigue score (0-100)"

    def _handle_workflow_choice(self, user_input: str) -> str:
        """Handle initial workflow selection."""
        lower_input = user_input.lower()

        if '1' in user_input or 'design' in lower_input or 'study' in lower_input:
            # Workflow 1: Forward (Test → Completes → Invitations)
            self.state.workflow = 'forward'
            self.current_step = 'research_question'
            return (
                "**Forward Planning: Study Design → Sample Size**\n\n"
                "I'll help you:\n"
                "1. Choose the right statistical test\n"
                "2. Calculate sample size needed\n"
                "3. Calculate invitations to send\n\n"
                "What are you trying to find out?\n\n"
                "Examples:\n"
                "- 'Compare satisfaction between two designs'\n"
                "- 'Test differences across user segments'\n"
                "- 'Predict churn from usage patterns'"
            )

        elif '2' in user_input or 'constraint' in lower_input or 'budget' in lower_input or 'feasib' in lower_input:
            # Workflow 2: Reverse (Constraints → Completes → Feasibility)
            self.state.workflow = 'reverse'
            self.current_step = 'survey_constraints'
            return (
                "**Reverse Planning: Constraints → Feasibility**\n\n"
                "I'll help you:\n"
                "1. Calculate sample from your survey constraints\n"
                "2. Check what statistical tests are feasible\n"
                "3. Suggest optimizations if underpowered\n\n"
                "**How many invitations can you send?**\n\n"
                "This is your email list size, participant pool, or budget limit.\n"
                "Example: '5000' or 'about 10000'"
            )

        elif '3' in user_input or 'quick' in lower_input or 'just' in lower_input or 'power only' in lower_input:
            # Workflow 3: Stats only (quick path)
            self.state.workflow = 'stats_only'
            self.current_step = 'research_question'
            return (
                "**Integrated Workflow** (Power + Survey + Invitations)\n\n"
                "I'll calculate:\n"
                "1. Required completes (statistical power)\n"
                "2. Expected drop-off (from survey design)\n"
                "3. Invitations to send\n\n"
                "Let's start with your research question.\n\n"
                "What are you trying to find out?\n\n"
                "Examples:\n"
                "- 'Compare satisfaction between two designs'\n"
                "- 'Test differences across user segments'\n"
                "- 'Predict behavior from demographics'"
            )

        else:
            return (
                "Please choose:\n\n"
                "Type '1' for **Statistical power only**\n"
                "Type '2' for **Integrated workflow** (power + survey + invitations)"
            )

    def _handle_research_question(self, user_input: str) -> str:
        """Analyze research question and infer study type."""
        self.state.research_question = user_input

        # Infer study type from keywords
        comparative_keywords = ['compare', 'difference', 'versus', 'vs', 'better', 'prefer',
                               'treatment', 'control', 'group', 'between']
        predictive_keywords = ['predict', 'influence', 'relationship', 'effect of',
                              'associated with', 'regression', 'cause']
        segment_keywords = ['segment', 'cluster', 'group', 'type', 'persona',
                           'class', 'profile', 'across']

        lower_input = user_input.lower()

        if any(keyword in lower_input for keyword in segment_keywords):
            self.state.study_type = 'segments'
            inferred_type = 'segment comparison'
        elif any(keyword in lower_input for keyword in comparative_keywords):
            self.state.study_type = 'comparative'
            inferred_type = 'comparing groups'
        elif any(keyword in lower_input for keyword in predictive_keywords):
            self.state.study_type = 'predictive'
            inferred_type = 'prediction/regression'
        else:
            # Default to comparative
            self.state.study_type = 'comparative'
            inferred_type = 'comparing groups'

        self.current_step = 'study_type_confirmation'

        return (
            f"Based on your question, it sounds like you're interested in **{inferred_type}**.\n\n"
            f"Is that correct? (yes/no)\n\n"
            f"If not, tell me which one:\n"
            f"1. Comparing groups (e.g., A vs B, treatment vs control)\n"
            f"2. Prediction/regression (e.g., what predicts outcome Y?)\n"
            f"3. Segment analysis (e.g., differences across user types)"
        )

    def _handle_study_type_confirmation(self, user_input: str) -> str:
        """Confirm or correct study type."""
        lower_input = user_input.lower()

        if 'yes' in lower_input or 'correct' in lower_input or 'right' in lower_input:
            # Confirmed, move to test details
            return self._ask_test_details()
        elif '1' in user_input or 'compar' in lower_input:
            self.state.study_type = 'comparative'
            return self._ask_test_details()
        elif '2' in user_input or 'predict' in lower_input or 'regress' in lower_input:
            self.state.study_type = 'predictive'
            return self._ask_test_details()
        elif '3' in user_input or 'segment' in lower_input:
            self.state.study_type = 'segments'
            return self._ask_test_details()
        else:
            return (
                "I didn't catch that. Please choose:\n"
                "1. Comparing groups\n"
                "2. Prediction/regression\n"
                "3. Segment analysis"
            )

    def _ask_test_details(self) -> str:
        """Ask for test-specific details."""
        self.current_step = 'test_details'

        if self.state.study_type == 'comparative':
            return (
                "How many groups are you comparing?\n"
                "- Enter '2' for two groups (e.g., A vs B)\n"
                "- Enter '3' or more for multiple groups (ANOVA)"
            )
        elif self.state.study_type == 'predictive':
            return (
                "How many predictors (independent variables) do you have?\n"
                "For example, if you're predicting satisfaction from price, quality, and ease-of-use, that's 3 predictors."
            )
        elif self.state.study_type == 'segments':
            return (
                "Tell me about your segments:\n"
                "- How many segments? (e.g., 3)\n"
                "- What percentage of the population is in each segment? (e.g., 40%, 40%, 20%)\n\n"
                "Format: '3 segments at 40, 40, 20'"
            )

    def _handle_test_details(self, user_input: str) -> str:
        """Process test-specific details."""
        if self.state.study_type == 'comparative':
            # Extract number of groups
            match = re.search(r'\d+', user_input)
            if match:
                self.state.n_groups = int(match.group())
                if self.state.n_groups == 2:
                    self.state.test_type = 'independent_ttest'
                else:
                    self.state.test_type = 'anova'
            else:
                return "Please enter the number of groups (e.g., 2 or 3)"

        elif self.state.study_type == 'predictive':
            # Extract number of predictors
            match = re.search(r'\d+', user_input)
            if match:
                self.state.n_predictors = int(match.group())
                self.state.test_type = 'multiple_regression'
            else:
                return "Please enter the number of predictors (e.g., 3)"

        elif self.state.study_type == 'segments':
            # Extract segments and prevalence - flexible parsing
            # Try multiple formats:
            # "3 segments at 40, 40, 20"
            # "60 30 10" (just numbers)
            # "60, 30, 10"

            # Look for "at" keyword to separate count from prevalence
            if ' at ' in user_input.lower():
                # Format: "3 segments at 60, 30, 10"
                parts = re.split(r'\s+at\s+', user_input, flags=re.IGNORECASE)
                if len(parts) == 2:
                    # Extract prevalence from part after "at"
                    prevalence_match = re.findall(r'(\d+(?:\.\d+)?)', parts[1])
                else:
                    prevalence_match = []
            else:
                # Format: just numbers "60 30 10" or "60, 30, 10"
                prevalence_match = re.findall(r'(\d+(?:\.\d+)?)', user_input)

            if len(prevalence_match) >= 2:
                # Parse prevalence values
                n_segments = len(prevalence_match)
                prevalence_values = [float(p) for p in prevalence_match]

                # Validate they look like percentages (0-100 range)
                if any(p > 100 for p in prevalence_values):
                    return (
                        f"❌ Prevalence values should be percentages (0-100).\n"
                        f"You entered: {prevalence_values}\n\n"
                        f"Try again with format: '60, 30, 10' or '3 segments at 60, 30, 10'"
                    )

                # Convert to proportions
                prevalence_values = [p / 100 for p in prevalence_values]

                # Check if they sum to ~100%
                total = sum(prevalence_values)

                # Strict validation - must sum to 95-105% (catch typos)
                if abs(total - 1.0) > 0.05:  # More than 5% off from 100%
                    return (
                        f"❌ Prevalence values should sum to 100%.\n"
                        f"You entered: {', '.join(prevalence_match)}% = {total*100:.0f}%\n\n"
                        f"Did you mean:\n"
                        f"- '60, 30, **10**' (sums to 100%)?\n\n"
                        f"Other valid examples:\n"
                        f"- '40, 40, 20'\n"
                        f"- '50, 30, 20'\n"
                        f"- '50, 50' (2 segments)"
                    )

                # Small normalization if very close (99-101%)
                if abs(total - 1.0) > 0.01:
                    prevalence_values = [p / total for p in prevalence_values]

                # Success! Store the segments
                self.state.segments = {
                    'n_segments': n_segments,
                    'prevalence': prevalence_values
                }
                self.state.test_type = 'segment_anova'

                # Confirm back to user
                prevalence_pct = [f"{p*100:.0f}%" for p in prevalence_values]
                confirmation = (
                    f"✅ Got it! {n_segments} segments with prevalence: {', '.join(prevalence_pct)}\n\n"
                    f"Moving on...\n\n"
                )
                return confirmation + self._ask_effect_size()

            else:
                return (
                    "Please specify segment prevalence values.\n\n"
                    "Examples:\n"
                    "- '3 segments at 60, 30, 10'\n"
                    "- '60, 30, 10'\n"
                    "- '40, 40, 20'"
                )

        # Move to effect size
        return self._ask_effect_size()

    def _ask_effect_size(self) -> str:
        """Ask about effect size."""
        self.current_step = 'effect_size'

        if self.state.test_type in ['independent_ttest', 'anova', 'segment_anova']:
            return (
                "What effect size do you expect?\n\n"
                "**Effect size guidelines (Cohen's d or f):**\n"
                "- Small: 0.2-0.25 (subtle difference)\n"
                "- Medium: 0.5 (moderate difference)\n"
                "- Large: 0.8+ (obvious difference)\n\n"
                "If unsure, 0.5 (medium) is a common choice.\n"
                "You can also say 'small', 'medium', or 'large'."
            )
        elif self.state.test_type == 'multiple_regression':
            return (
                "What effect size do you expect?\n\n"
                "**Effect size guidelines (f² or R²):**\n"
                "- Small: f²=0.02 (R²=0.02, explains 2% of variance)\n"
                "- Medium: f²=0.15 (R²=0.13, explains 13% of variance)\n"
                "- Large: f²=0.35 (R²=0.26, explains 26% of variance)\n\n"
                "If unsure, 0.15 (medium) is a common choice.\n"
                "You can also say 'small', 'medium', or 'large'."
            )

    def _handle_effect_size(self, user_input: str) -> str:
        """Process effect size input."""
        lower_input = user_input.lower()

        # Handle text inputs
        if 'small' in lower_input:
            if self.state.test_type in ['independent_ttest', 'anova', 'segment_anova']:
                self.state.effect_size = 0.2 if self.state.test_type == 'independent_ttest' else 0.1
            else:
                self.state.effect_size = 0.02
        elif 'medium' in lower_input or 'moderate' in lower_input:
            if self.state.test_type in ['independent_ttest', 'anova', 'segment_anova']:
                self.state.effect_size = 0.5 if self.state.test_type == 'independent_ttest' else 0.25
            else:
                self.state.effect_size = 0.15
        elif 'large' in lower_input:
            if self.state.test_type in ['independent_ttest', 'anova', 'segment_anova']:
                self.state.effect_size = 0.8 if self.state.test_type == 'independent_ttest' else 0.4
            else:
                self.state.effect_size = 0.35
        else:
            # Try to parse as number
            match = re.search(r'(\d+(?:\.\d+)?)', user_input)
            if match:
                self.state.effect_size = float(match.group())
            else:
                return "Please enter a number or say 'small', 'medium', or 'large'"

        # In integrated workflow, always calculate (don't ask about existing n)
        if self.state.workflow == 'integrated':
            self.state.has_existing_n = False
            return self._ask_survey_availability()

        # In stats-only workflow, ask if they want to check power of existing n
        self.current_step = 'existing_n'
        return (
            "Do you already have a sample size in mind, or do you want me to calculate one?\n\n"
            "- **Calculate one** (recommended) → I'll tell you what you need\n"
            "- **I have a number** → I'll check if it's adequate\n\n"
            "Type 'calculate' or enter your sample size"
        )

    def _handle_existing_n(self, user_input: str) -> str:
        """Handle existing sample size question."""
        lower_input = user_input.lower()

        if 'calculate' in lower_input or 'no' in lower_input or "don't" in lower_input:
            self.state.has_existing_n = False
            # Skip to survey availability
            return self._ask_survey_availability()
        else:
            # Try to extract number
            match = re.search(r'(\d+)', user_input)
            if match:
                n = int(match.group())

                # Validate reasonable range
                if n < 10:
                    return (
                        f"❌ Sample size of {n} is too small for meaningful analysis.\n"
                        f"Minimum recommended: 10 per group\n\n"
                        f"Did you mean a larger number?"
                    )
                if n > 100000:
                    return (
                        f"❌ Sample size of {n:,} seems unusually large.\n"
                        f"Please double-check your entry.\n\n"
                        f"If correct, type the number again to confirm."
                    )

                self.state.has_existing_n = True
                self.state.existing_n = n
                return self._ask_survey_availability()
            else:
                return "Please enter a number or say 'calculate'"

    def _ask_survey_availability(self) -> str:
        """Ask if they have a survey to audit."""

        # In integrated workflow, always ask for survey
        if self.state.workflow == 'integrated':
            self.state.has_survey = True
            self.current_step = 'fatigue_score'
            return (
                "Great! Now let's account for survey drop-off.\n\n"
                "**What's your expected drop-off rate or completion rate?**\n\n"
                "You can provide either:\n"
                "- **Drop-off rate:** e.g., '30%' or '0.30' → 30% abandon\n"
                "- **Completion rate:** e.g., '70% complete' → 70% finish\n\n"
                "**Reference ranges:**\n"
                "- Simple survey (<10 min): 5-15% drop-off\n"
                "- Typical survey (10-15 min): 15-25% drop-off\n"
                "- Complex survey (loops/grids): 25-40% drop-off\n"
                "- Very complex (>20 min): 40-60% drop-off"
            )

        # In stats-only workflow, make survey optional
        self.current_step = 'survey_availability'
        return (
            "Do you have a survey designed?\n\n"
            "- **Yes** → I'll calculate invitations needed (accounting for drop-off)\n"
            "- **No** → We're done (completes only)\n\n"
            "Type 'yes' or 'no'"
        )

    def _handle_survey_availability(self, user_input: str) -> str:
        """Handle survey availability."""
        lower_input = user_input.lower()

        if 'yes' in lower_input:
            self.state.has_survey = True
            self.current_step = 'fatigue_score'
            return (
                "Great! What's your expected drop-off or completion rate?\n\n"
                "You can provide either:\n"
                "- **Drop-off rate:** e.g., '30%' or '0.30'\n"
                "- **Completion rate:** e.g., '70% complete'\n\n"
                "**Reference ranges:**\n"
                "- Simple survey: 5-15% drop-off (85-95% complete)\n"
                "- Typical survey: 15-25% drop-off (75-85% complete)\n"
                "- Complex survey: 25-40% drop-off (60-75% complete)"
            )
        else:
            self.state.has_survey = False
            # Run power analysis and finish
            return self._run_power_analysis()

    def _handle_fatigue_score(self, user_input: str) -> str:
        """Handle drop-off/completion rate input."""
        # Try to parse number
        match = re.search(r'(\d+(?:\.\d+)?)', user_input)
        if not match:
            return (
                "❌ Please enter a number.\n\n"
                "Examples:\n"
                "- '30%' or '0.30' → 30% drop-off\n"
                "- '70% complete' → 70% completion (30% drop-off)"
            )

        value = float(match.group())
        lower_input = user_input.lower()

        # Detect if user provided completion rate vs drop-off rate
        # Keywords: "complete", "finish", "success", "respond" → completion rate
        is_completion_rate = any(word in lower_input for word in ['complete', 'finish', 'success', 'respond'])

        # Convert to drop-off rate (0.0-1.0 scale)
        if is_completion_rate:
            # User gave completion rate → convert to drop-off
            if value > 1:  # Percentage format (e.g., 70%)
                dropoff_rate = (100 - value) / 100
            else:  # Decimal format (e.g., 0.70)
                dropoff_rate = 1 - value
        else:
            # User gave drop-off rate
            if value > 1:  # Percentage format (e.g., 30%)
                dropoff_rate = value / 100
            else:  # Decimal format (e.g., 0.30)
                dropoff_rate = value

        # Validate range
        if not (0 <= dropoff_rate <= 1):
            return (
                f"❌ Rate should be between 0-100% (or 0.0-1.0).\n"
                f"You entered: {value}\n\n"
                "Examples:\n"
                "- '30%' or '0.30' → 30% drop-off\n"
                "- '70% complete' → 30% drop-off"
            )

        # Store as drop-off rate (0.0-1.0)
        # Note: Still using fatigue_score field for backwards compat, but now it's dropoff_rate
        self.state.fatigue_score = dropoff_rate

        # Now ask about CTR
        self.current_step = 'ctr'
        return (
            f"Got it! Drop-off rate: {dropoff_rate:.1%}\n\n"
            f"One more thing: **What's your expected click-through rate (CTR)?**\n\n"
            f"CTR = % of people who click your survey invitation link\n\n"
            f"**Realistic ranges:**\n"
            f"- No incentive: ~1% or below\n"
            f"- Standard email: 2-5%\n"
            f"- With prize draw: 5-10%\n"
            f"- Best case (prize draw): ~10%\n\n"
            f"**For intercept surveys (in-app pop-ups):** Type 'skip' (no link click needed)\n\n"
            f"**Unsure?** Ask ResearchOps or check past campaign analytics.\n\n"
            f"Enter as percentage (e.g., '5%') or decimal (e.g., '0.05')\n"
            f"Or type 'skip' if no email link involved"
        )

    def _handle_ctr(self, user_input: str) -> str:
        """Handle CTR input."""
        lower_input = user_input.lower()

        # Allow skipping (means CTR = 1.0 - direct access)
        if 'skip' in lower_input or '100' in user_input or 'direct' in lower_input:
            self.state.ctr = 1.0
            return self._run_integrated_analysis()

        # Parse number
        match = re.search(r'(\d+(?:\.\d+)?)', user_input)
        if not match:
            return (
                "❌ Please enter a number.\n\n"
                "Examples:\n"
                "- '5%' or '0.05' → 5% CTR\n"
                "- 'skip' → Direct access (no link needed)"
            )

        value = float(match.group())

        # Convert to rate (0.0-1.0 scale)
        if value > 1:  # Percentage format
            ctr = value / 100
        else:  # Decimal format
            ctr = value

        # Validate range - CTR typically 1-10%
        if ctr > 0.10:
            return (
                f"⚠️ CTR of {ctr:.0%} seems unusually high.\n\n"
                f"Realistic CTR is typically 1-10% (10% with prize draw is best case).\n\n"
                f"Did you mean:\n"
                f"- '{value:.0f}%' (as decimal: {value/100:.2f})?\n"
                f"- Skip (intercept survey, no email link)?\n\n"
                f"Or type the value again to confirm."
            )

        if not (0 < ctr <= 1):
            return (
                f"❌ CTR should be between 0.1-20% (or 0.001-0.20).\n"
                f"You entered: {value}\n\n"
                "Examples:\n"
                "- '5%' → 5% CTR\n"
                "- '0.05' → 5% CTR"
            )

        # Warn if very low
        if ctr < 0.01:
            return (
                f"⚠️ CTR of {ctr:.1%} is very low.\n\n"
                f"This will require a very large invitation list.\n\n"
                f"Did you mean '{value*100:.0f}%' instead of '{value}%'?\n\n"
                f"Or type the value again to confirm."
            )

        self.state.ctr = ctr
        return self._run_integrated_analysis()

    def _run_power_analysis(self) -> str:
        """Run power analysis based on collected information."""
        from .calculators.means import MeansPowerCalc
        from .calculators.regression import RegressionPowerCalc
        from .calculators.segments import SegmentPowerCalc

        # Show what we're about to calculate
        summary = self._generate_summary()

        try:
            if self.state.test_type == 'independent_ttest':
                calc = MeansPowerCalc(test_type='independent')
                if self.state.has_existing_n:
                    result = calc.calculate(
                        effect_size=self.state.effect_size,
                        alpha=self.state.alpha,
                        n=self.state.existing_n,
                        solve_for='power'
                    )
                    return self._format_power_result(result)
                else:
                    result = calc.calculate(
                        effect_size=self.state.effect_size,
                        alpha=self.state.alpha,
                        power=self.state.power,
                        solve_for='n'
                    )
                    return self._format_sample_size_result(result)

            elif self.state.test_type == 'anova':
                calc = MeansPowerCalc(test_type='anova')
                if self.state.has_existing_n:
                    result = calc.calculate(
                        effect_size=self.state.effect_size,
                        alpha=self.state.alpha,
                        n=self.state.existing_n,
                        solve_for='power',
                        n_groups=self.state.n_groups
                    )
                    return self._format_power_result(result)
                else:
                    result = calc.calculate(
                        effect_size=self.state.effect_size,
                        alpha=self.state.alpha,
                        power=self.state.power,
                        solve_for='n',
                        n_groups=self.state.n_groups
                    )
                    return self._format_sample_size_result(result)

            elif self.state.test_type == 'multiple_regression':
                calc = RegressionPowerCalc(test_type='multiple')
                if self.state.has_existing_n:
                    result = calc.calculate(
                        effect_size=self.state.effect_size,
                        alpha=self.state.alpha,
                        n=self.state.existing_n,
                        solve_for='power',
                        n_predictors=self.state.n_predictors
                    )
                    return self._format_power_result(result)
                else:
                    result = calc.calculate(
                        effect_size=self.state.effect_size,
                        alpha=self.state.alpha,
                        power=self.state.power,
                        solve_for='n',
                        n_predictors=self.state.n_predictors
                    )
                    return self._format_sample_size_result(result)

            elif self.state.test_type == 'segment_anova':
                calc = SegmentPowerCalc(
                    n_segments=self.state.segments['n_segments'],
                    prevalence=self.state.segments['prevalence'],
                    test_type='anova'
                )
                if self.state.has_existing_n:
                    result = calc.calculate(
                        effect_size=self.state.effect_size,
                        alpha=self.state.alpha,
                        total_n=self.state.existing_n,
                        solve_for='power'
                    )
                    return self._format_power_result(result)
                else:
                    result = calc.calculate(
                        effect_size=self.state.effect_size,
                        alpha=self.state.alpha,
                        power=self.state.power,
                        solve_for='n'
                    )
                    return summary + self._format_sample_size_result(result)

        except Exception as e:
            return f"Error running power analysis: {str(e)}"

    def _run_integrated_analysis(self) -> str:
        """Run integrated power + drop-off + CTR analysis."""
        # First run power analysis
        power_response = self._run_power_analysis()

        # Then add funnel integration
        from .integrations.dropoff import integrated_sample_plan

        # Get power result (re-run to get dict)
        power_result = self._get_power_result()

        if power_result:
            # Use dropoff_rate and CTR directly
            sample_plan = integrated_sample_plan(
                power_result=power_result,
                dropoff_rate=self.state.fatigue_score,  # Now stores dropoff_rate (0.0-1.0)
                ctr=self.state.ctr if self.state.ctr else 1.0,
                response_rate=1.0,
                buffer=0.0
            )

            # Build funnel visualization
            funnel_section = f"\n\n**📊 Survey Funnel Analysis**\n\n"

            # Show funnel breakdown
            funnel_section += "**Survey Funnel:**\n"
            funnel_section += f"1. **Invitations sent:** {sample_plan['sample_plan']['invitations_needed']}\n"

            if self.state.ctr and self.state.ctr < 1.0:
                funnel_section += f"2. **Expected clicks:** {sample_plan['sample_plan']['expected_clicks']} "
                funnel_section += f"({sample_plan['sample_plan']['ctr']:.1%} CTR)\n"
                funnel_section += f"3. **Expected starts:** {sample_plan['sample_plan']['expected_starts']}\n"
                funnel_section += f"4. **Expected completes:** {sample_plan['sample_plan']['expected_completes']} "
            else:
                funnel_section += f"2. **Expected starts:** {sample_plan['sample_plan']['expected_starts']}\n"
                funnel_section += f"3. **Expected completes:** {sample_plan['sample_plan']['expected_completes']} "

            funnel_section += f"({sample_plan['sample_plan']['completion_rate']:.1%} complete)\n\n"

            # Summary metrics
            funnel_section += "**Key Metrics:**\n"
            if self.state.ctr and self.state.ctr < 1.0:
                funnel_section += f"- CTR: {sample_plan['sample_plan']['ctr']:.1%}\n"
            funnel_section += f"- Drop-off rate: {sample_plan['fatigue_audit']['estimated_dropoff_rate']:.1%} "
            funnel_section += f"({sample_plan['fatigue_audit']['risk_level']} risk)\n"
            funnel_section += f"- Overall conversion: {sample_plan['sample_plan']['effective_rate']:.1%} "
            funnel_section += f"(invitation → complete)\n\n"

            funnel_section += "**Recommendations:**\n"
            for rec in sample_plan['recommendations']:
                funnel_section += f"- {rec}\n"

            return power_response + funnel_section

        return power_response

    def _get_power_result(self) -> Optional[Dict]:
        """Get power result dict (helper for integrated analysis)."""
        from .calculators.means import MeansPowerCalc
        from .calculators.regression import RegressionPowerCalc
        from .calculators.segments import SegmentPowerCalc

        try:
            if self.state.test_type == 'independent_ttest':
                calc = MeansPowerCalc(test_type='independent')
                return calc.calculate(
                    effect_size=self.state.effect_size,
                    alpha=self.state.alpha,
                    power=self.state.power,
                    solve_for='n' if not self.state.has_existing_n else 'power',
                    n=self.state.existing_n if self.state.has_existing_n else None
                )
            elif self.state.test_type == 'anova':
                calc = MeansPowerCalc(test_type='anova')
                return calc.calculate(
                    effect_size=self.state.effect_size,
                    alpha=self.state.alpha,
                    power=self.state.power,
                    solve_for='n' if not self.state.has_existing_n else 'power',
                    n=self.state.existing_n if self.state.has_existing_n else None,
                    n_groups=self.state.n_groups
                )
            elif self.state.test_type == 'multiple_regression':
                calc = RegressionPowerCalc(test_type='multiple')
                return calc.calculate(
                    effect_size=self.state.effect_size,
                    alpha=self.state.alpha,
                    power=self.state.power,
                    solve_for='n' if not self.state.has_existing_n else 'power',
                    n=self.state.existing_n if self.state.has_existing_n else None,
                    n_predictors=self.state.n_predictors
                )
            elif self.state.test_type == 'segment_anova':
                calc = SegmentPowerCalc(
                    n_segments=self.state.segments['n_segments'],
                    prevalence=self.state.segments['prevalence'],
                    test_type='anova'
                )
                return calc.calculate(
                    effect_size=self.state.effect_size,
                    alpha=self.state.alpha,
                    power=self.state.power,
                    solve_for='n' if not self.state.has_existing_n else 'power',
                    total_n=self.state.existing_n if self.state.has_existing_n else None
                )
        except:
            return None

    def _format_sample_size_result(self, result: Dict) -> str:
        """Format sample size calculation result."""
        output = "**✅ Power Analysis Complete!**\n\n"

        if 'total_n' in result:
            output += f"**Required Sample Size:** {result['total_n']}\n"
            if 'n_per_group' in result:
                output += f"({result['n_per_group']} per group)\n"
        elif 'n' in result:
            output += f"**Required Sample Size:** {result['n']}\n"
        elif 'n_per_group' in result:
            output += f"**Required Sample Size:** {result['n_per_group']} per group\n"

        output += f"\n**Study Parameters:**\n"
        output += f"- Power: {self.state.power:.0%}\n"
        output += f"- Significance level (α): {self.state.alpha}\n"

        if 'effect_size' in result:
            output += f"- Effect size: {result['effect_size']:.2f}\n"
        elif 'effect_size_f2' in result:
            output += f"- Effect size (f²): {result['effect_size_f2']:.2f}\n"
            output += f"- Equivalent R²: {result.get('r_squared', 0):.2f}\n"

        # Add segment-specific details
        if 'n_per_segment' in result:
            output += f"\n**Sample per segment:**\n"
            for i, n in enumerate(result['n_per_segment']):
                prev = self.state.segments['prevalence'][i]
                output += f"- Segment {i+1} ({prev:.0%}): {n} participants\n"

        output += "\n*Next step: If you have a survey, run the fatigue audit to estimate drop-off.*"

        return output

    def _format_power_result(self, result: Dict) -> str:
        """Format power calculation result."""
        output = "**✅ Power Analysis Complete!**\n\n"

        output += f"**Statistical Power:** {result['power']:.1%}\n"

        if result['power'] >= 0.80:
            output += "✅ Your sample size is adequate (≥80% power)\n"
        elif result['power'] >= 0.70:
            output += "⚠️ Marginally adequate power (70-80%)\n"
        else:
            output += "❌ Underpowered (< 70%). Consider increasing sample size.\n"

        output += f"\n**Study Parameters:**\n"
        output += f"- Sample size: {self.state.existing_n}\n"
        output += f"- Significance level (α): {self.state.alpha}\n"

        if 'effect_size' in result:
            output += f"- Effect size: {result['effect_size']:.2f}\n"
        elif 'effect_size_f2' in result:
            output += f"- Effect size (f²): {result['effect_size_f2']:.2f}\n"

        return output

    def _handle_back(self) -> str:
        """Handle back/undo command."""
        if len(self.state.history) < 2:
            return (
                "You're at the beginning. Nothing to go back to.\n\n"
                "Type 'restart' to start over."
            )

        # Remove last two entries (current step and user input)
        self.state.history = self.state.history[:-1]

        # Get previous step
        if self.state.history:
            prev_step, _ = self.state.history[-1]
            self.current_step = prev_step

        # Clear related state based on step
        if self.current_step == 'workflow_choice':
            self.state.workflow = None
        elif self.current_step == 'research_question':
            self.state.study_type = None
            self.state.test_type = None
        elif self.current_step == 'test_details':
            self.state.n_groups = None
            self.state.n_predictors = None
            self.state.segments = None
        elif self.current_step == 'effect_size':
            self.state.effect_size = None

        # Re-ask the question for current step
        if self.current_step == 'workflow_choice':
            return self.start_conversation()
        elif self.current_step == 'research_question':
            return (
                "↩️ Going back...\n\n"
                "What are you trying to find out?\n\n"
                "Examples:\n"
                "- 'Compare satisfaction between two designs'\n"
                "- 'Test differences across user segments'\n"
                "- 'Predict behavior from demographics'"
            )
        else:
            return "↩️ Went back one step. (Feature in development - may need to restart)"

    def _generate_summary(self) -> str:
        """Generate summary of collected information before calculation."""
        summary = "📋 **Summary of Your Study:**\n\n"

        if self.state.test_type:
            test_names = {
                'independent_ttest': 'Independent t-test',
                'anova': 'One-way ANOVA',
                'multiple_regression': 'Multiple regression',
                'segment_anova': 'Segment comparison (ANOVA)'
            }
            summary += f"**Test:** {test_names.get(self.state.test_type, self.state.test_type)}\n"

        if self.state.n_groups:
            summary += f"**Groups:** {self.state.n_groups}\n"

        if self.state.n_predictors:
            summary += f"**Predictors:** {self.state.n_predictors}\n"

        if self.state.segments:
            prevalence_pct = [f"{p*100:.0f}%" for p in self.state.segments['prevalence']]
            summary += f"**Segments:** {self.state.segments['n_segments']} at {', '.join(prevalence_pct)}\n"

        if self.state.effect_size:
            summary += f"**Effect size:** {self.state.effect_size}\n"

        summary += f"**Significance level:** α = {self.state.alpha}\n"
        summary += f"**Desired power:** {self.state.power:.0%}\n"

        if self.state.fatigue_score:
            summary += f"**Survey fatigue:** {self.state.fatigue_score:.0f}/100\n"

        summary += "\n🔄 **Calculating...**\n\n"

        return summary

    def _handle_survey_constraints(self, user_input: str) -> str:
        """Handle invitations available (reverse workflow)."""
        match = re.search(r'(\d+)', user_input.replace(',', ''))
        if match:
            invitations = int(match.group())
            self.state.existing_n = invitations  # Store for later

            self.current_step = 'ctr_reverse'
            return (
                f"Got it! **{invitations:,} invitations** available.\n\n"
                f"**What's your expected click-through rate (CTR)?**\n\n"
                f"Typical ranges:\n"
                f"- No incentive: 1% or below\n"
                f"- Standard email: 2-5%\n"
                f"- With incentive: 5-10%\n"
                f"- Intercept survey (in-app): 100% (type 'skip' or '100')\n\n"
                f"Type a percentage (e.g., '5' for 5%) or 'skip' for intercept surveys."
            )
        else:
            return "Please enter the number of invitations you can send (e.g., '5000')"

    def _handle_ctr_reverse(self, user_input: str) -> str:
        """Handle CTR in reverse workflow."""
        lower_input = user_input.lower()

        if 'skip' in lower_input or '100' in user_input:
            self.state.ctr = 1.0
            ctr_display = "100% (intercept survey)"
        else:
            match = re.search(r'(\d+(?:\.\d+)?)', user_input)
            if match:
                ctr_value = float(match.group())
                if ctr_value > 1:
                    ctr_value = ctr_value / 100
                self.state.ctr = ctr_value
                ctr_display = f"{ctr_value:.1%}"
            else:
                return "Please enter a CTR percentage (e.g., '5' for 5%) or 'skip' for intercept surveys"

        self.current_step = 'dropoff_reverse'
        return (
            f"Got it! CTR: **{ctr_display}**\n\n"
            f"**What's your expected drop-off rate?**\n\n"
            f"(% who start but don't finish)\n\n"
            f"Typical ranges:\n"
            f"- Simple survey: 5-15%\n"
            f"- Standard survey: 15-25%\n"
            f"- Complex survey (loops/grids): 25-40%\n\n"
            f"Type a percentage (e.g., '30' for 30%)"
        )

    def _handle_dropoff_reverse(self, user_input: str) -> str:
        """Handle drop-off rate and calculate completes, then check feasibility."""
        match = re.search(r'(\d+(?:\.\d+)?)', user_input)
        if match:
            dropoff_value = float(match.group())
            if dropoff_value > 1:
                dropoff_value = dropoff_value / 100
            self.state.fatigue_score = dropoff_value  # Store as decimal

            # Calculate completes
            invitations = self.state.existing_n
            clicks = int(invitations * self.state.ctr)
            starts = clicks
            completes = int(starts * (1 - dropoff_value))

            # Store sample for test feasibility
            self.state.existing_n = completes

            result = (
                f"Got it! Drop-off: **{dropoff_value:.0%}**\n\n"
                f"**📊 Survey Funnel Results:**\n\n"
                f"1. Invitations: {invitations:,}\n"
                f"2. Expected clicks: {clicks:,} ({self.state.ctr:.1%} CTR)\n"
                f"3. Expected starts: {starts:,}\n"
                f"4. Expected completes: **{completes:,}** ({(1-dropoff_value):.0%} completion)\n\n"
                f"Overall conversion: {completes/invitations:.1%} (invitation → complete)\n\n"
            )

            # Now check test feasibility
            self.current_step = 'research_question'
            result += (
                f"**You'll get {completes:,} completes.**\n\n"
                f"Now let's check what you can test with this sample size.\n\n"
                f"**What are you trying to find out?**\n\n"
                f"Examples:\n"
                f"- 'Compare satisfaction between two designs'\n"
                f"- 'Test differences across user segments'\n"
                f"- 'Predict churn from usage patterns'"
            )

            return result
        else:
            return "Please enter a drop-off percentage (e.g., '30' for 30%)"
