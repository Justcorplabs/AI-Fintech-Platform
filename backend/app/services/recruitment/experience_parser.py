from typing import List, Dict, Any
import re


class ExperienceParser:
    BULLET_PREFIX = re.compile(r"^\s*(?:[-•*●▪▫◦]|\d+[\).])\s*")

    DATE_PATTERN = re.compile(
        r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s*)?"
        r"(?:20\d{2}|19\d{2})"
        r"(?:\s*(?:-|–|—|to)\s*"
        r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s*)?"
        r"(?:20\d{2}|19\d{2}|present|current))?",
        re.IGNORECASE,
    )

    ROLE_WORDS = [
        "intern", "trainee", "assistant", "officer", "analyst", "clerk",
        "consultant", "administrator", "accountant", "finance", "accounting",
        "data", "monitoring", "evaluation", "meal", "attachment", "internship",
        "cashier", "sales", "security", "technician", "developer",
    ]

    ORG_WORDS = [
        "ministry", "council", "company", "services", "department",
        "authority", "university", "college", "bank", "holdings", "pvt",
        "ltd", "limited", "organisation", "organization", "agency",
        "corporation", "foundation", "trust", "gweru", "harare",
        "environmental management agency", "nutrition action zimbabwe",
    ]

    def parse(self, lines: List[str]) -> List[Dict[str, Any]]:
        logical_lines = self._join_wrapped_lines(lines)

        entries = []
        current = None
        pending_role = None
        pending_org = None

        i = 0
        while i < len(logical_lines):
            line = logical_lines[i]

            if self._is_noise(line):
                i += 1
                continue

            is_bullet = self._is_bullet(line)
            period = self._extract_period(line)

            if not is_bullet and self._looks_like_role(line):
                if current and current.get("bullets"):
                    entries.append(current)

                role = self._remove_period(line, period).strip(" |,-–—")
                next_line = logical_lines[i + 1] if i + 1 < len(logical_lines) else ""
                next_period = self._extract_period(next_line)

                if next_line and not self._is_bullet(next_line) and self._looks_like_organisation(next_line):
                    org = self._remove_period(next_line, next_period).strip(" |,-–—")
                    current = self._new_entry(role, org, period or next_period)
                    i += 2
                    continue

                current = self._new_entry(role, "", period)
                i += 1
                continue

            if not is_bullet and self._looks_like_organisation(line):
                org = self._remove_period(line, period).strip(" |,-–—")

                if current and not current.get("organisation"):
                    current["organisation"] = org
                    if period and not current.get("period"):
                        current["period"] = period
                elif current and current.get("bullets"):
                    entries.append(current)
                    current = self._new_entry("Relevant Experience", org, period)
                else:
                    pending_org = org

                i += 1
                continue

            if period and not is_bullet and len(line.split()) <= 8:
                if current and not current.get("period"):
                    current["period"] = period
                elif pending_role or pending_org:
                    current = self._new_entry(
                        pending_role or "Relevant Experience",
                        pending_org or "",
                        period,
                    )
                    pending_role = None
                    pending_org = None

                i += 1
                continue

            bullet = self._clean_bullet(line)

            if bullet:
                if current is None:
                    current = self._new_entry(
                        pending_role or "Relevant Experience",
                        pending_org or "",
                        "",
                    )
                    pending_role = None
                    pending_org = None

                current["bullets"].append(bullet)

            i += 1

        if current:
            entries.append(current)

        return self._post_process(entries)

    def _join_wrapped_lines(self, lines: List[str]) -> List[str]:
        cleaned = [self._clean_raw_line(line) for line in lines if self._clean_raw_line(line)]
        output = []

        for line in cleaned:
            if not output:
                output.append(line)
                continue

            previous = output[-1]
            starts_new_bullet = self._is_bullet(line)
            starts_new_role = self._looks_like_role(line)
            starts_new_org = self._looks_like_organisation(line)
            has_date = bool(self._extract_period(line))

            previous_looks_open = (
                not previous.endswith((".", ":", ";"))
                or previous.lower().endswith(("and", "or", "to", "for", "with", "of", "under"))
            )

            is_label_continuation = previous.lower().endswith(
                ("problem solved:", "approach:", "results:", "recommendation:", "tools and methods:")
            )

            if starts_new_bullet or starts_new_role or starts_new_org or has_date:
                output.append(line)
            elif previous_looks_open or is_label_continuation:
                output[-1] = previous + " " + line
            else:
                output.append(line)

        return output

    def _new_entry(self, role: str, organisation: str, period: str) -> Dict[str, Any]:
        return {
            "role": self._clean_label(role) or "Relevant Experience",
            "organisation": self._clean_label(organisation),
            "period": period or "",
            "bullets": [],
        }

    def _post_process(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        output = []

        for entry in entries:
            role = self._clean_label(entry.get("role", ""))
            organisation = self._clean_label(entry.get("organisation", ""))
            period = entry.get("period", "") or ""

            bullets = []
            for bullet in entry.get("bullets", []):
                clean = self._clean_bullet(bullet)

                if not clean:
                    continue

                if self._looks_like_role(clean) and len(clean.split()) <= 8:
                    continue

                if self._looks_like_organisation(clean) and len(clean.split()) <= 8:
                    continue

                if clean not in bullets:
                    bullets.append(clean)

            if not role and not bullets:
                continue

            output.append(
                {
                    "role": role or "Relevant Experience",
                    "organisation": organisation,
                    "period": period,
                    "bullets": bullets[:10],
                }
            )

        merged = []

        for entry in output:
            if merged and self._same_entry(merged[-1], entry):
                for bullet in entry["bullets"]:
                    if bullet not in merged[-1]["bullets"]:
                        merged[-1]["bullets"].append(bullet)
                if not merged[-1].get("period") and entry.get("period"):
                    merged[-1]["period"] = entry["period"]
            else:
                merged.append(entry)

        return merged[:8]

    def _same_entry(self, a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        a_key = (a.get("role", "") + a.get("organisation", "")).lower().strip()
        b_key = (b.get("role", "") + b.get("organisation", "")).lower().strip()
        return bool(a_key and b_key and a_key == b_key)

    def _is_bullet(self, line: str) -> bool:
        return bool(self.BULLET_PREFIX.match(line))

    def _clean_raw_line(self, line: str) -> str:
        value = str(line or "").strip()
        value = value.replace("", "•")
        value = re.sub(r"\s+", " ", value)
        return value.strip()

    def _clean_bullet(self, line: str) -> str:
        value = self._clean_raw_line(line)
        value = self.BULLET_PREFIX.sub("", value)
        value = value.strip(" -–—|•*")
        value = re.sub(r"\s+", " ", value)
        return value

    def _clean_label(self, value: str) -> str:
        value = self._clean_bullet(value)
        value = re.sub(r"\s+", " ", value)
        return value.strip(" |,-–—")

    def _extract_period(self, line: str) -> str:
        match = self.DATE_PATTERN.search(line or "")
        return match.group(0).strip() if match else ""

    def _remove_period(self, line: str, period: str) -> str:
        if not period:
            return line
        return line.replace(period, "").strip()

    def _looks_like_role(self, line: str) -> bool:
        lower = line.lower()

        if self._is_bullet(line):
            return False

        if len(line.split()) > 10:
            return False

        return any(word in lower for word in self.ROLE_WORDS)

    def _looks_like_organisation(self, line: str) -> bool:
        lower = line.lower()

        if self._is_bullet(line):
            return False

        if len(line.split()) > 12:
            return False

        return any(word in lower for word in self.ORG_WORDS)

    def _is_noise(self, line: str) -> bool:
        lower = line.lower().strip()

        noise = {
            "work experience",
            "professional experience",
            "employment history",
            "experience",
            "industrial attachment",
            "internship",
        }

        return lower in noise


experience_parser = ExperienceParser()