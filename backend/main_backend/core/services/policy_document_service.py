"""Generate and expose issued policy PDF documents for the main backend."""

from __future__ import annotations

from pathlib import Path

from commons.logger import logger

logging = logger(__name__)


class PolicyDocumentService:
    """Builds simple policy PDF documents and returns their public URLs."""

    def __init__(self) -> None:
        """Initialise the document service and ensure its output folder exists."""

        self.base_dir = Path(__file__).resolve().parents[2]
        self.output_dir = self.base_dir / "generated_policies"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_policy_pdf(
        self,
        policy_number: str,
        user_id: str,
        company_name: str,
        plan_name: str,
        payment_reference: str,
        total_premium: float,
        start_date: str,
        end_date: str,
    ) -> str:
        """Generate a simple PDF file for an issued policy and return its URL.

        Args:
            policy_number: Business-facing policy number.
            user_id: User identifier who owns the policy.
            company_name: Issuing insurance company name.
            plan_name: Issued insurance plan name.
            payment_reference: Linked payment reference.
            total_premium: Final premium paid for the policy.
            start_date: Policy start date string.
            end_date: Policy end date string.

        Returns:
            str: Public URL path for the generated PDF file.

        Raises:
            OSError: If the PDF file cannot be written.
        """

        try:
            logging.info(
                "Executing PolicyDocumentService.generate_policy_pdf for policy %s",
                policy_number,
            )
            file_name = f"{policy_number}.pdf"
            file_path = self.output_dir / file_name
            lines = [
                "InsureFlow Policy Document",
                f"Policy Number: {policy_number}",
                f"User ID: {user_id}",
                f"Company: {company_name}",
                f"Plan: {plan_name}",
                f"Payment Reference: {payment_reference}",
                f"Total Premium: {total_premium:.2f}",
                f"Start Date: {start_date}",
                f"End Date: {end_date}",
            ]
            file_path.write_bytes(self._build_pdf_bytes(lines))
            return f"/generated-policies/{file_name}"
        except OSError as error:
            logging.error(
                "Error in PolicyDocumentService.generate_policy_pdf for policy %s: %s",
                policy_number,
                error,
            )
            raise

    def _build_pdf_bytes(self, lines: list[str]) -> bytes:
        """Create a minimal PDF document containing the provided text lines."""

        escaped_lines = [self._escape_pdf_text(line) for line in lines]
        content_lines = ["BT", "/F1 14 Tf", "50 760 Td"]
        for index, line in enumerate(escaped_lines):
            if index == 0:
                content_lines.append(f"({line}) Tj")
            else:
                content_lines.append("0 -24 Td")
                content_lines.append(f"({line}) Tj")
        content_lines.append("ET")
        content_stream = "\n".join(content_lines).encode("ascii")

        objects = [
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
            (
                b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
            ),
            (
                f"4 0 obj\n<< /Length {len(content_stream)} >>\nstream\n".encode("ascii")
                + content_stream
                + b"\nendstream\nendobj\n"
            ),
            b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        ]

        pdf = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for obj in objects:
            offsets.append(len(pdf))
            pdf.extend(obj)

        xref_offset = len(pdf)
        pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        pdf.extend(
            (
                f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n"
                f"{xref_offset}\n%%EOF"
            ).encode("ascii")
        )
        return bytes(pdf)

    def _escape_pdf_text(self, value: str) -> str:
        """Escape characters that are special inside a PDF text stream."""

        return (
            value.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )
