import json
import os
import shapefile
import geopandas as gpd
import sys

shpfilepath=sys.argv[1]
##e.g., /mnt/rdf/jcm10/riedeltest/JohnTestFiles/JohnTestBlocks.shp

tmp = gpd.GeoDataFrame.from_file(shpfilepath)
tmpWGS84 = tmp.to_crs({'proj':'longlat', 'ellps':'WGS84', 'datum':'WGS84'})
tmpWGS84.to_file('tmp.shp')
sf = shapefile.Reader("tmp.shp")
shapeRecs = sf.shapeRecords()
geoj = json.dumps(shapeRecs.__geo_interface__)
d = open('%s.json' %(os.path.basename(shpfilepath)[0:-4]),'w')

d.write(geoj)
d.close()


