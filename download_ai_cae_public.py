import os
from pathlib import Path

from literature_finder.downloader import SafeDownloader
from literature_finder.models import LiteratureRecord


project_dir = Path(__file__).resolve().parent
output_dir = Path(
    os.environ.get(
        "AI_CAE_OUTPUT_DIR", project_dir / "outputs" / "ai_cae_2021_2026"
    )
)

# These are the 18 records marked as having a public, lawful full-text route.
# URLs are direct PDF/archive endpoints where available; the downloader still
# verifies HTTP status, content type, PDF signature, and file size.
downloadable = {
    2: ("Reduced Order Machine Learning Finite Element Methods: Concept, Implementation, and Future Applications", "2021", "https://par.nsf.gov/servlets/purl/10300074"),
    3: ("On-the-fly construction of surrogate constitutive models for concurrent multiscale mechanical analysis through probabilistic machine learning", "2021", "https://pure.tudelft.nl/ws/files/86670210/1_s2.0_S2590055220300354_main.pdf"),
    4: ("Teaching solid mechanics to artificial intelligence—a fast solver for heterogeneous materials", "2021", "https://www.nature.com/articles/s41524-021-00571-z.pdf"),
    8: ("Data-driven synchronization-avoiding algorithms in the explicit distributed structural analysis of soft tissue", "2022", "https://arxiv.org/pdf/2207.02194"),
    11: ("Surrogate modeling of parametrized finite element simulations with varying mesh topology using recurrent neural networks", "2022", "https://www.sciencedirect.com/science/article/pii/S259000562200008X/pdfft?isDTMRedir=true&download=true"),
    12: ("Multi-fidelity surrogate modeling through hybrid machine learning for biomechanical and finite element analysis of soft tissues", "2022", "https://shayansss.github.io/files/2022_09.pdf"),
    15: ("Learning finite element convergence with the Multi-fidelity Graph Neural Network", "2022", "https://par.nsf.gov/servlets/purl/10436360"),
    19: ("Physics-Informed Neural Networks for Shell Structures", "2022", "https://arxiv.org/pdf/2207.14291"),
    20: ("Finite Element Method-enhanced Neural Network for Forward and Inverse Problems", "2022", "https://arxiv.org/pdf/2205.08321"),
    21: ("A data-driven reduced-order surrogate model for entire elastoplastic simulations applied to representative volume elements", "2023", "https://www.nature.com/articles/s41598-023-38104-x.pdf"),
    22: ("Topology optimization with advanced CNN using mapped physics-based data", "2023", "https://link.springer.com/content/pdf/10.1007/s00158-022-03461-0.pdf"),
    27: ("Graph Neural Network enhanced Finite Element modelling", "2023", "https://publications.rwth-aachen.de/record/954759/files/954759.pdf"),
    28: ("Low-dimensional data-based surrogate model of a continuum-mechanical musculoskeletal system based on non-intrusive model order reduction", "2023", "https://arxiv.org/pdf/2302.06528"),
    29: ("Physics Informed Surrogate Model for Linear Elasticity", "2023", "https://journals.sagepub.com/doi/pdf/10.3233/ATDE230121"),
    31: ("Mesh-Informed Neural Networks for Operator Learning in Finite Element Spaces", "2023", "https://link.springer.com/content/pdf/10.1007/s10915-023-02331-1.pdf"),
    35: ("Comparison of neural FEM and neural operator methods for applications in solid mechanics", "2024", "https://link.springer.com/content/pdf/10.1007/s00521-024-10132-2.pdf"),
    44: ("Transfer learning-enhanced finite element-integrated neural networks", "2025", "https://ira.lib.polyu.edu.hk/bitstream/10397/112007/1/1-s2.0-S0020740325001614-main.pdf"),
    50: ("A surrogate model for topology optimisation of elastic structures via parametric autoencoders", "2026", "https://upcommons.upc.edu/server/api/core/bitstreams/6f5228a7-8729-4bc8-9121-c4d6b4a26ee7/content"),
}

records = [LiteratureRecord(title=f"placeholder-{i}") for i in range(1, 51)]
for sequence, (title, year, url) in downloadable.items():
    literature_type = {
        8: "预印本",
        19: "预印本",
        20: "预印本",
        27: "会议论文",
        29: "会议论文",
        35: "综述",
    }.get(sequence, "期刊论文")
    records[sequence - 1] = LiteratureRecord(
        title=title,
        publication_date=year,
        literature_type=literature_type,
        best_access_url=url,
        download_url=url,
        download_source="verified public full-text route",
        download_file_type="pdf",
        download_permission_verified=True,
        authors=["paper"],
    )

selected = set(downloadable)
results = SafeDownloader(timeout=45.0, retries=2, min_interval=1.5).download(
    records, output_dir, selected=selected
)
for result in results:
    print(result.sequence, result.status, result.filename, result.failure_reason)
print("downloaded", sum(result.status == "downloaded" for result in results))
print("already_exists", sum(result.status == "already_exists" for result in results))
print("failed", sum(result.status == "failed" for result in results))
print("folder", output_dir)
