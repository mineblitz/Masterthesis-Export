from __future__ import annotations

from pathlib import Path
import os

from marker.config.parser import ConfigParser
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import save_output


_APPROVAL_PREFIXES = ("z-", "z_", "p-", "p_")
_LLM_SERVICE_PATH = "app.services.components.marker_openrouter_service.OpenRouterService"


_OUTPUT_EXTENSIONS = {
    "markdown": ".md",
    "json": ".json",
    "html": ".html",
}


def _apply_surya_transformers_compatibility_patch() -> None:
    """
    Work around surya-ocr config init incompatibility with newer transformers.

    transformers may instantiate config classes with no kwargs for diff logging.
    SuryaOCRConfig expects nested encoder/decoder kwargs, so we mark it as
    no-default-init to skip that no-arg instantiation path.
    """
    try:
        from surya.recognition.model.config import SuryaOCRConfig

        SuryaOCRConfig.has_no_defaults_at_init = True
    except Exception:
        # If internals change, keep conversion behavior unchanged and fail naturally later.
        return


def _resolve_output_file(
    source_pdf: Path,
    output_dir: Path,
    output_format: str,
    *,
    use_llm: bool,
) -> Path:
    suffix = "_marker_llm" if use_llm else "_marker"
    extension = _OUTPUT_EXTENSIONS.get(output_format)
    if extension is None:
        raise ValueError(
            f"Unsupported output_format '{output_format}'. Supported formats: {', '.join(sorted(_OUTPUT_EXTENSIONS))}"
        )
    return output_dir / f"{source_pdf.stem}{suffix}{extension}"


def _is_approval_pdf(pdf_path: Path) -> bool:
    return pdf_path.suffix.lower() == ".pdf" and pdf_path.name.lower().startswith(_APPROVAL_PREFIXES)


def find_approval_pdfs(root_dir: str | Path) -> list[Path]:
    root_path = Path(root_dir).resolve()

    if not root_path.exists():
        raise FileNotFoundError(f"Root directory not found: {root_path}")

    approval_pdfs = [pdf_path for pdf_path in root_path.rglob("*.pdf") if _is_approval_pdf(pdf_path)]
    return sorted(approval_pdfs, key=lambda pdf_path: pdf_path.as_posix())


def convert_single_pdf_with_marker(
    pdf_path: str | Path,
    output_dir: str | Path,
    *,
    output_format: str = "markdown",
    use_llm: bool = False,
    llm_model: str = "google/gemma-4-26b-a4b-it",
    skip_existing: bool = True,
) -> Path:
    """
    Convert a single PDF with Marker without LLM and write a static output file.

    The function is intentionally single-file/single-run oriented so it can be used
    for one-time static conversions.
    """
    source_pdf = Path(pdf_path).resolve()
    target_dir = Path(output_dir).resolve()

    if not source_pdf.exists():
        raise FileNotFoundError(f"PDF not found: {source_pdf}")
    if not _is_approval_pdf(source_pdf):
        raise ValueError(
            "Marker conversion is restricted to approval PDFs with filenames starting with z-, z_, p-, or p_. "
            f"Received: {source_pdf.name}"
        )

    output_file = _resolve_output_file(source_pdf, target_dir, output_format, use_llm=use_llm)
    if skip_existing and output_file.exists():
        return output_file

    target_dir.mkdir(parents=True, exist_ok=True)
    _apply_surya_transformers_compatibility_patch()

    config_options: dict[str, object] = {
        "output_format": output_format,
        "output_dir": str(target_dir),
        "disable_image_extraction": False,
        "use_llm": use_llm,
    }
    llm_service = None
    if use_llm:
        from app.settings import settings

        openrouter_api_key = (
            settings.openrouter_api_key
            or settings.open_router_api_key
            or settings.open_router_api_key_free
            or os.getenv("OPEN_ROUTER_API_KEY")
            or os.getenv("OPEN_ROUTER_API_KEY_FREE")
        )
        if not openrouter_api_key:
            raise RuntimeError(
                "OPEN_ROUTER_API_KEY (or OPEN_ROUTER_API_KEY_FREE) is missing from the environment or .env file."
            )

        config_options.update(
            {
                "llm_service": _LLM_SERVICE_PATH,
                "openrouter_base_url": settings.openrouter_base_url,
                "openrouter_api_key": openrouter_api_key,
                "openrouter_model": llm_model,
            }
        )
        llm_service = _LLM_SERVICE_PATH

    config_parser = ConfigParser(config_options)
    config_dict = config_parser.generate_config_dict()
    if use_llm:
        config_dict.update(
            {
                "openrouter_base_url": config_options["openrouter_base_url"],
                "openrouter_api_key": config_options["openrouter_api_key"],
                "openrouter_model": config_options["openrouter_model"],
            }
        )

    converter = PdfConverter(
        config=config_dict,
        artifact_dict=create_model_dict(),
        processor_list=config_parser.get_processors(),
        renderer=config_parser.get_renderer(),
        llm_service=llm_service,
    )

    rendered = converter(str(source_pdf))
    save_output(rendered, str(target_dir), output_file.stem)

    return output_file


def run_single_static_conversion() -> Path:
    """
    Run one static conversion for a single PDF path in system-information.

    Adjust the PDF path if you want to target another file.
    """
    return convert_single_pdf_with_marker(
        pdf_path=Path("system-information") / "a" / "files" / "a_montageanleitung.pdf",
        output_dir=Path("system-information") / "a" / "files",
    )


def convert_approval_pdfs_with_marker(
    root_dir: str | Path,
    *,
    output_format: str = "markdown",
    use_llm: bool = False,
    llm_model: str = "google/gemma-4-26b-a4b-it",
    skip_existing: bool = True,
) -> list[Path]:
    root_path = Path(root_dir).resolve()
    approval_pdfs = find_approval_pdfs(root_path)

    output_files: list[Path] = []
    for pdf_path in approval_pdfs:
        output_file = _resolve_output_file(
            pdf_path,
            pdf_path.parent,
            output_format,
            use_llm=use_llm,
        )
        if skip_existing and output_file.exists():
            output_files.append(output_file)
            continue

        output_files.append(
            convert_single_pdf_with_marker(
                pdf_path=pdf_path,
                output_dir=pdf_path.parent,
                output_format=output_format,
                use_llm=use_llm,
                llm_model=llm_model,
                skip_existing=skip_existing,
            )
        )

    return output_files


def convert_approval_pdfs_with_marker_llm(
    root_dir: str | Path,
    *,
    llm_model: str = "google/gemma-4-26b-a4b-it",
    skip_existing: bool = True,
) -> list[Path]:
    return convert_approval_pdfs_with_marker(
        root_dir,
        output_format="markdown",
        use_llm=True,
        llm_model=llm_model,
        skip_existing=skip_existing,
    )


convert_single_pdf_with_marker_llm = convert_single_pdf_with_marker


if __name__ == "__main__":
    result = run_single_static_conversion()
    print(f"Marker conversion completed: {result}")
