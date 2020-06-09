# © 2019 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

import logging
from decimal import Decimal

import pikepdf
import pytest
from PIL import Image

from ocrmypdf._exec.ghostscript import rasterize_pdf
from ocrmypdf.exceptions import ExitCode
from ocrmypdf.helpers import Resolution

check_ocrmypdf = pytest.helpers.check_ocrmypdf
run_ocrmypdf = pytest.helpers.run_ocrmypdf
run_ocrmypdf_api = pytest.helpers.run_ocrmypdf_api


@pytest.fixture
def francais(resources):
    path = resources / 'francais.pdf'
    return path, pikepdf.open(path)


def test_rasterize_size(francais, outdir, caplog):
    path, pdf = francais
    page_size_pts = (pdf.pages[0].MediaBox[2], pdf.pages[0].MediaBox[3])
    assert pdf.pages[0].MediaBox[0] == pdf.pages[0].MediaBox[1] == 0
    page_size = (page_size_pts[0] / Decimal(72), page_size_pts[1] / Decimal(72))
    target_size = Decimal('50.0'), Decimal('30.0')
    forced_dpi = Resolution(42.0, 4242.0)

    rasterize_pdf(
        path,
        outdir / 'out.png',
        raster_device='pngmono',
        raster_dpi=Resolution(
            target_size[0] / page_size[0], target_size[1] / page_size[1]
        ),
        page_dpi=forced_dpi,
    )

    with Image.open(outdir / 'out.png') as im:
        assert im.size == target_size
        assert im.info['dpi'] == forced_dpi


def test_rasterize_rotated(francais, outdir, caplog):
    path, pdf = francais
    page_size_pts = (pdf.pages[0].MediaBox[2], pdf.pages[0].MediaBox[3])
    assert pdf.pages[0].MediaBox[0] == pdf.pages[0].MediaBox[1] == 0
    page_size = (page_size_pts[0] / Decimal(72), page_size_pts[1] / Decimal(72))
    target_size = Decimal('50.0'), Decimal('30.0')
    forced_dpi = Resolution(42.0, 4242.0)

    caplog.set_level(logging.DEBUG)
    rasterize_pdf(
        path,
        outdir / 'out.png',
        raster_device='pngmono',
        raster_dpi=Resolution(
            target_size[0] / page_size[0], target_size[1] / page_size[1]
        ),
        page_dpi=forced_dpi,
        rotation=90,
    )

    with Image.open(outdir / 'out.png') as im:
        assert im.size == (target_size[1], target_size[0])
        assert im.info['dpi'] == (forced_dpi[1], forced_dpi[0])


def test_gs_render_failure(resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'blank.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_render_failure.py',
    )
    assert 'Casper is not a friendly ghost' in err
    assert p.returncode == ExitCode.child_process_error


def test_gs_raster_failure(resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_raster_failure.py',
    )
    assert 'Ghost story archive not found' in err
    assert p.returncode == ExitCode.child_process_error


def test_ghostscript_pdfa_failure(resources, outpdf):
    p, out, err = run_ocrmypdf(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_pdfa_failure.py',
    )
    assert (
        p.returncode == ExitCode.pdfa_conversion_failed
    ), "Unexpected return when PDF/A fails"


def test_ghostscript_feature_elision(resources, outpdf):
    check_ocrmypdf(
        resources / 'francais.pdf',
        outpdf,
        '--plugin',
        'tests/plugins/tesseract_noop.py',
        '--plugin',
        'tests/plugins/gs_feature_elision.py',
    )
