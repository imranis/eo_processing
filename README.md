# Earth Observatory

A Python/Streamlit app for exploring Sentinel-2 imagery. Draw a polygon, choose dates, sign in to Copernicus and select true colour (TCC), false colour (FCC), cloud-masked variants, NDVI or NBR. Results include previews, enhancement histograms and scientific GeoTIFF downloads. The notebook also supports Sentinel-1 SAR.

## Run locally

Use Python 3.12 or 3.13:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

If an existing Conda installation reports a PROJ database version conflict, start with `env -u PROJ_LIB -u PROJ_DATA streamlit run app.py` to use the virtual environment’s bundled geospatial data.

Open the local URL printed by Streamlit. Select **Sign in with Copernicus**, open the verification link and enter the displayed code if asked. Use your own [Copernicus Data Space account](https://dataspace.copernicus.eu/). Complete verification within five minutes. This app never asks for your password.

Draw exactly one polygon, select products and click **Run analysis**. Processing runs remotely in your Copernicus account and consumes your quota. The app submits one batch job at a time, checks progress every five seconds and downloads finished results. Use **Cancel analysis** to stop the active job and remaining queue.

Keep the tab open during processing. Browser refresh/disconnection or a server restart can lose the session and job tracking; a submitted remote job may continue. Its ID is displayed while active, and you can manage jobs in the [openEO Web Editor](https://editor.openeo.org/). Results are temporary: old directories are removed after one hour of inactivity during subsequent app activity or status refreshes; a new analysis or logout removes the previous run. Download anything you want to keep.

## Publish on Streamlit Community Cloud

1. Commit and push the application files to `ihpwapp/eo_processing` on GitHub. Do not include credentials, `.streamlit/secrets.toml`, virtual environments or local generated imagery.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) and connect the GitHub account that can access the repository.
3. Create an app, select the repository and branch containing these changes, and set the entry point to `app.py`.
4. In Advanced settings, select Python **3.13** (the locally tested version). Deploy, and enable public viewing in the app's sharing settings.
5. Open the assigned `https://….streamlit.app` URL in a fresh browser, sign in to Copernicus and run a small analysis before sharing it.

No server-owned Copernicus password or token is required. Each visitor signs in independently. Streamlit Community Cloud supplies the shareable URL; a local server is not a public deployment. Free hosting has resource limits and is intended here for a bounded prototype, not guaranteed availability or large parallel workloads.

See the [official deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

### Configuration

Optional environment variables (or top-level Community Cloud secrets):

| Setting | Default | Meaning |
| --- | --- | --- |
| `EO_MAX_AREA_KM2` | `100` | Maximum geodesic bounding-box area |
| `EO_MAX_DAYS` | `90` | Maximum date interval in days |

Dates use an inclusive start and exclusive end, and the end must be later than the start. Invalid/self-intersecting polygons, polygons crossing the date line, future end dates and oversized requests are rejected. Each browser session can have one active run. There is no durable job history or database.

## Notebook and Python API

```sh
pip install -r requirements-notebook.txt
jupyter notebook run.ipynb
```

The notebook initializes its connection once per kernel session. Every processing function now requires that connection and an explicit output directory:

```python
import tempfile
import openeo
import matplotlib.pyplot as plt
import functions2

connection = openeo.connect('https://openeo.dataspace.copernicus.eu').authenticate_oidc()
output_dir = tempfile.mkdtemp(prefix='eo-analysis-')
result = functions2.ndvi(connection, polygon, '2024-01-01', '2024-02-01', output_dir)
display(result.figure)
plt.close(result.figure)
print(result.rasters, result.preview)
```

The seven functions are `tcc`, `tcc_masked`, `fcc`, `fcc_masked`, `nbr`, `ndvi`, and `sar`. They return a `ProcessingResult` containing raster paths, a preview path and a caller-owned figure. Notebook calls wait for job completion, with a one-hour timeout. `submit_product` creates an unstarted job; the web controller records it before starting, polls without blocking the whole UI, then calls `collect_product`.

## Processing details

- Optical data: `SENTINEL2_L2A`, temporal mean, clipped to the selected polygon. Resolution follows the collection/backend and selected bands; it is not uniformly 30 m.
- TCC RGB: B04/B03/B02. FCC RGB: B08/B04/B03.
- Cloud-masked composites exclude SCL classes 3 (shadow), 8/9 (cloud), and 10 (cirrus), then remove SCL before compositing.
- NDVI: `(B08 - B04) / (B08 + B04)`; NBR: `(B08 - B12) / (B08 + B12)`, calculated from temporal mean bands. The index outputs are not cloud-masked in this version.
- GeoTIFFs retain scientific values. RGB previews use a 0–6000 display range and BCET enhancement; index previews use a 5th–95th percentile stretch. Nodata is excluded from histograms; constant arrays are handled safely.
- SAR uses mean sigma0-ellipsoid backscatter, converted to dB, with separate VV/VH panels.

Connections are stored only in each Streamlit session, never in a shared cache. Device login explicitly disables refresh-token disk storage. Expired access requires reauthentication: use **Reconnect to Copernicus** to resume checking the same remote job without submitting another. Logout clears session credentials and local results after stopping an active job. Do not enable SDK debug logging on a public deployment because authentication diagnostics can contain sensitive information.

## Validation

```sh
python -m unittest discover -s tests -v
```

Tests cover SDK process graphs, colour band order, polygon masks, connection reuse, nodata handling, validation, session isolation, job submission/polling/cancellation, uncertain starts, expired access and temporary-file cleanup. Live integration additionally requires an interactive Copernicus account and available quota; no credentials are bundled in the repository.

Author: Imran Idham Sabki
