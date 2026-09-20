import openeo

connection = openeo.connect(url="openeo.dataspace.copernicus.eu")
connection.authenticate_oidc()
