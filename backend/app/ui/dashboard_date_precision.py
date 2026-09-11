"""Preserve source date precision in the employee dashboard presentation."""

_FORMAT_DEADLINE_OLD = r'''    function formatDeadline(value) {
      if (!value) return { label: "Ei ilmoitettu", className: "" };
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return { label: "Ei ilmoitettu", className: "" };
      const days = Math.ceil((date.getTime() - Date.now()) / 86400000);
      const label = new Intl.DateTimeFormat("fi-FI", { dateStyle: "medium", timeStyle: "short" }).format(date);
      if (days < 0) return { label, className: "deadline-past" };
      if (days <= 7) return { label, className: "deadline-soon" };
      return { label, className: "" };
    }'''

_FORMAT_DEADLINE_NEW = r'''    function parseDateOnly(value) {
      const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || "").trim());
      if (!match) return null;
      const year = Number(match[1]);
      const month = Number(match[2]);
      const day = Number(match[3]);
      const date = new Date(year, month - 1, day, 12, 0, 0);
      if (
        date.getFullYear() !== year ||
        date.getMonth() !== month - 1 ||
        date.getDate() !== day
      ) return null;
      return date;
    }

    function formatDateFact(exactValue, dateOnlyValue) {
      if (exactValue) return formatDateTime(exactValue);
      const date = parseDateOnly(dateOnlyValue);
      if (!date) return "Ei tietoa";
      return new Intl.DateTimeFormat("fi-FI", { dateStyle: "medium" }).format(date);
    }

    function formatDeadline(exactValue, dateOnlyValue) {
      let date = null;
      let hasExactTime = false;
      if (exactValue) {
        const exactDate = new Date(exactValue);
        if (!Number.isNaN(exactDate.getTime())) {
          date = exactDate;
          hasExactTime = true;
        }
      }
      if (!date) date = parseDateOnly(dateOnlyValue);
      if (!date) return { label: "Ei ilmoitettu", className: "" };

      const now = new Date();
      const deadlineDay = Date.UTC(date.getFullYear(), date.getMonth(), date.getDate());
      const today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
      const days = Math.floor((deadlineDay - today) / 86400000);
      const label = hasExactTime
        ? new Intl.DateTimeFormat("fi-FI", { dateStyle: "medium", timeStyle: "short" }).format(date)
        : new Intl.DateTimeFormat("fi-FI", { dateStyle: "medium" }).format(date);
      if (days < 0) return { label, className: "deadline-past" };
      if (days <= 7) return { label, className: "deadline-soon" };
      return { label, className: "" };
    }'''

_DEADLINE_CALL_OLD = (
    "        const deadline = formatDeadline("
    "call.application_deadline_at || call.application_deadline_on);"
)
_DEADLINE_CALL_NEW = (
    "        const deadline = formatDeadline("
    "call.application_deadline_at, call.application_deadline_on);"
)

_OPENING_DETAIL_OLD = (
    '      grid.append(detailBox("Haku avautuu", '
    "formatDateTime(detail.application_opens_at)));"
)
_OPENING_DETAIL_NEW = (
    '      grid.append(detailBox("Haku avautuu", '
    "formatDateFact(detail.application_opens_at, detail.application_opens_on)));"
)


def _replace_once(html: str, old: str, new: str, *, label: str) -> str:
    if old not in html:
        raise RuntimeError(f"Dashboard date-precision sentinel missing: {label}")
    return html.replace(old, new, 1)


def render_dashboard_date_precision(html: str) -> str:
    """Keep date-only facts date-only and exact timestamps exact in the UI."""

    html = _replace_once(
        html,
        _FORMAT_DEADLINE_OLD,
        _FORMAT_DEADLINE_NEW,
        label="deadline-formatter",
    )
    html = _replace_once(
        html,
        _DEADLINE_CALL_OLD,
        _DEADLINE_CALL_NEW,
        label="deadline-call",
    )
    return _replace_once(
        html,
        _OPENING_DETAIL_OLD,
        _OPENING_DETAIL_NEW,
        label="opening-detail",
    )
