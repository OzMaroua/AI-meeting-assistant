import json
import os


class MeetingState:

    def __init__(self):
        self.summary = ""
        self.topics = []
        self.decisions = []
        self.action_items = []
        self.open_questions = []

    def update(self, new_analysis):

        if new_analysis.get("summary"):
            self.summary = new_analysis["summary"]

        self.topics.extend(
            new_analysis.get("topics", [])
        )

        self.decisions.extend(
            new_analysis.get("decisions", [])
        )

        self.action_items.extend(
            new_analysis.get("action_items", [])
        )

        self.open_questions.extend(
            new_analysis.get("open_questions", [])
        )

    def to_dict(self):

        return {
            "summary": self.summary,
            "topics": self.topics,
            "decisions": self.decisions,
            "action_items": self.action_items,
            "open_questions": self.open_questions,
        }

    def save(self, path):

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.to_dict(),
                f,
                ensure_ascii=False,
                indent=4
            )