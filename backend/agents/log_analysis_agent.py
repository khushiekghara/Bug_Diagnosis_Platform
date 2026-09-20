"""
Milestone 2 - Task 2: Log Analysis Agent

This agent analyzes stack traces and error logs.

It identifies:
1. Exception / error type
2. Failure point
3. Affected code path
4. Confidence score
5. Reasoning

The implementation uses regular expressions.
No external API or LLM is required.
"""

import re
from typing import Dict, List, Optional


# =========================================================
# 1. EXCEPTION PATTERNS
# =========================================================

EXCEPTION_PATTERNS = [

    # Generic Python / Java / other Exception or Error
    r"\b([A-Za-z_][A-Za-z0-9_]*(?:Exception|Error|Fault|Failure))\b",

    # Common specific exceptions
    r"\b(NullPointerException|IndexOutOfBoundsException|ClassCastException)\b",

    r"\b(TypeError|ValueError|KeyError|IndexError|AttributeError|ImportError)\b",

    r"\b(SyntaxError|ReferenceError|RangeError)\b",

    # Other common errors
    r"\b(SegmentationFault|Segfault|NullReferenceException)\b",
]


# =========================================================
# 2. FILE + LINE NUMBER PATTERNS
# =========================================================

FRAME_PATTERNS = [

    # Python traceback
    #
    # Example:
    # File "app/main.py", line 42
    #
    r'File\s+"([^"]+\.(?:py|java|js|ts|cpp|c|cs|go|rb))",\s*line\s*(\d+)',

    # Generic format
    #
    # Example:
    # app/main.py:42
    #
    r"(?P<file>[\w./\\-]+\.(?:py|java|js|ts|cpp|c|cs|go|rb)):(?P<line>\d+)",

    # Java / JavaScript stack trace
    #
    # Example:
    # at com.example.UserService.load(UserService.java:120)
    #
    r"at\s+[\w.$<>/-]+\((?P<file>[\w./\\-]+\.(?:java|js|ts|kt)):(?P<line>\d+)(?::\d+)?\)",

    # JavaScript / Node.js format
    #
    # Example:
    # at /src/user.js:17:9
    #
    r"at\s+(?P<file>[/\w.\-\\]+\.(?:js|ts)):(?P<line>\d+)(?::\d+)?",
]


# =========================================================
# 3. EXTRACT EXCEPTION TYPE
# =========================================================

def extract_exception_type(text: str) -> Optional[str]:

    """
    Search the text for a recognizable exception/error type.

    Returns:
        Exception name as string
        OR
        None if no exception is detected.
    """

    for pattern in EXCEPTION_PATTERNS:

        match = re.search(
            pattern,
            text
        )

        if match:

            return match.group(1)

    return None


# =========================================================
# 4. EXTRACT FILE + LINE FRAMES
# =========================================================

def extract_file_frames(text: str) -> List[Dict]:

    """
    Extract file names and line numbers from stack traces.

    Returns a list such as:

    [
        {
            "file": "app/main.py",
            "line": "42"
        },
        {
            "file": "app/db.py",
            "line": "17"
        }
    ]
    """

    frames = []

    # Used to prevent duplicate frames
    seen = set()

    for pattern in FRAME_PATTERNS:

        for match in re.finditer(
            pattern,
            text
        ):

            groups = match.groupdict()

            # Patterns using named groups
            if groups:

                file_path = groups["file"]

                line_number = groups["line"]

            # Patterns using normal groups
            else:

                file_path, line_number = match.groups()

            key = (
                file_path,
                str(line_number)
            )

            # Avoid duplicate entries
            if key not in seen:

                seen.add(key)

                frames.append(
                    {
                        "file": file_path,
                        "line": str(line_number)
                    }
                )

    return frames


# =========================================================
# 5. IDENTIFY FAILURE POINT
# =========================================================

def guess_failure_point(
    frames: List[Dict],
    exception_type: Optional[str]
) -> str:

    """
    Determine the most likely failure location.

    If stack frames are available, the last frame is used
    as the closest available failure point.

    If no frame exists but an exception exists, the location
    cannot be determined.
    """

    if frames:

        last_frame = frames[-1]

        return (
            f"{last_frame['file']} "
            f"(line {last_frame['line']})"
        )

    if exception_type:

        return (
            f"Unknown location -- "
            f"exception type '{exception_type}' "
            f"was identified"
        )

    return (
        "Unable to determine -- "
        "no stack trace or file references found"
    )


# =========================================================
# 6. IDENTIFY AFFECTED CODE PATH
# =========================================================

def guess_affected_code_path(
    frames: List[Dict]
) -> List[str]:

    """
    Create a list of unique files involved in the stack trace.
    """

    seen = []

    for frame in frames:

        file_path = frame["file"]

        if file_path not in seen:

            seen.append(file_path)

    return seen


# =========================================================
# 7. LOG ANALYSIS AGENT
# =========================================================

class LogAnalysisAgent:

    """
    Log Analysis Agent.

    It analyzes:
    - Stack traces
    - Error logs
    - Error messages

    And returns structured information.
    """

    def run(
        self,
        bug_report: Dict
    ) -> Dict:

        # -------------------------------------------------
        # Combine stack trace and error log
        # -------------------------------------------------

        log_text = " ".join(
            [
                bug_report.get(
                    "stack_trace",
                    ""
                ) or "",

                bug_report.get(
                    "error_log",
                    ""
                ) or "",
            ]
        ).strip()

        # -------------------------------------------------
        # If no logs exist, use description
        # -------------------------------------------------

        if not log_text:

            log_text = (
                bug_report.get(
                    "description",
                    ""
                ) or ""
            )

        # -------------------------------------------------
        # Nothing available for analysis
        # -------------------------------------------------

        if not log_text.strip():

            return {

                "agent":
                    "LogAnalysisAgent",

                "exception_type":
                    None,

                "failure_point":
                    "No stack trace or error log provided",

                "affected_code_path":
                    [],

                "raw_frames_found":
                    0,

                "confidence":
                    0.30,

                "reasoning":
                    "No log or stack trace text "
                    "was available to analyze."
            }

        # -------------------------------------------------
        # Extract exception
        # -------------------------------------------------

        exception_type = extract_exception_type(
            log_text
        )

        # -------------------------------------------------
        # Extract stack frames
        # -------------------------------------------------

        frames = extract_file_frames(
            log_text
        )

        # -------------------------------------------------
        # Find failure point
        # -------------------------------------------------

        failure_point = guess_failure_point(
            frames,
            exception_type
        )

        # -------------------------------------------------
        # Find affected code paths
        # -------------------------------------------------

        affected_paths = guess_affected_code_path(
            frames
        )

        # -------------------------------------------------
        # Calculate confidence
        # -------------------------------------------------

        evidence_score = 0

        if exception_type:

            evidence_score += 0.5

        if frames:

            evidence_score += 0.5

        confidence = round(
            max(
                evidence_score,
                0.30
            ),
            2
        )

        # -------------------------------------------------
        # Generate reasoning
        # -------------------------------------------------

        reasoning_parts = []

        if exception_type:

            reasoning_parts.append(
                f"Detected exception/error type "
                f"'{exception_type}' using "
                f"pattern matching."
            )

        else:

            reasoning_parts.append(
                "No recognizable exception/error "
                "type was found."
            )

        if frames:

            reasoning_parts.append(
                f"Found {len(frames)} file/line "
                f"frame(s); the last frame is used "
                f"as the likely failure point."
            )

        else:

            reasoning_parts.append(
                "No file/line references "
                "were found."
            )

        # -------------------------------------------------
        # Return structured result
        # -------------------------------------------------

        return {

            "agent":
                "LogAnalysisAgent",

            "exception_type":
                exception_type,

            "failure_point":
                failure_point,

            "affected_code_path":
                affected_paths,

            "raw_frames_found":
                len(frames),

            "frames":
                frames,

            "confidence":
                confidence,

            "reasoning":
                " ".join(reasoning_parts)
        }


# =========================================================
# 8. TEST THE AGENT
# =========================================================

if __name__ == "__main__":

    sample_bug = {

        "title":
            "Database connection failure",

        "description":
            "",

        "stack_trace":
            (
                'Traceback (most recent call last):\n'

                '  File "app/main.py", line 42, '
                'in start\n'

                '  File "app/db.py", line 17, '
                'in connect\n'

                'ConnectionError: '
                'could not reach database'
            ),

        "error_log":
            "",
    }

    # Create agent
    agent = LogAnalysisAgent()

    # Run analysis
    result = agent.run(
        sample_bug
    )

    # Print result
    import json

    print(
        json.dumps(
            result,
            indent=4
        )
    )