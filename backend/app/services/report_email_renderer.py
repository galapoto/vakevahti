from html import escape

from app.api.report_schemas import FundingReportResponse


def render_report_email_html(report: FundingReportResponse) -> str:
    """Render an email-safe VAKE-branded HTML alternative for a report."""

    title = escape(report.title)
    body = escape(report.email_body or "").replace("\n", "<br>")
    item_count = len(report.items)
    return f"""<!doctype html>
<html lang="fi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
</head>
<body style="margin:0;background:#f5f6f8;color:#20242a;font-family:Poppins,Calibri,Arial,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
    <tr>
      <td align="center" style="padding:28px 12px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
               style="max-width:720px;background:#ffffff;border-radius:18px;overflow:hidden;border:1px solid #e7e6ef;">
          <tr>
            <td style="height:8px;background:#312783;font-size:0;line-height:0;">&nbsp;</td>
          </tr>
          <tr>
            <td style="padding:30px 34px 22px;">
              <div style="font-size:13px;font-weight:600;letter-spacing:.04em;color:#E6007E;">
                VAKEHYVÄ · VAKEVAHTI
              </div>
              <h1 style="margin:8px 0 8px;font-size:28px;line-height:1.2;font-weight:700;color:#312783;">
                {title}
              </h1>
              <p style="margin:0;color:#5F6B6D;font-size:14px;line-height:1.6;">
                {item_count} rahoituslöydöstä · automaattisesti muodostettu raporttipohja
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 34px 30px;">
              <div style="border-left:5px solid #76CBF3;padding:20px 22px;background:#f8fbfd;border-radius:0 12px 12px 0;font-size:15px;line-height:1.7;">
                {body}
              </div>
              <p style="margin:24px 0 0;font-size:12px;line-height:1.6;color:#6a7075;">
                Tämä viesti on muodostettu VakeVahdin tallennetuista rahoituslöydöksistä.
                Raporttia voidaan muokata ennen mahdollista uutta lähetystä.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 34px;background:#312783;color:#ffffff;font-size:12px;line-height:1.5;">
              Vantaan ja Keravan hyvinvointialue · VakeVahti
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
