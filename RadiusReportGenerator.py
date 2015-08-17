# This program was written as the final project for GEOG 485
# Summer semester 2015, by Anna Garrett. 
#
# It will only run with Galveston CAD shapefiles.
#
# Please email me if you have any questions: agarrett@galvestoncad.org

import arcpy
import os
import sys

# define target datasets, id, mxd container, buffer distance
# reference[0]
filePath = sys.path[0]
targetDataset = os.path.join(filePath, 'gilchrist.shp') 
stCenterline = os.path.join(filePath, 'gilchrist_streets.shp')
idField = raw_input('Please input account number, R######') # define the field that contains the account number. this version will work with R# used by the galveston county's tax assessor

# ********** checking for correctly formatted account number **********
# reference[1]
if idField.startswith('R'):
    pass
else:
    idField = raw_input('Account number needs "R"')
# ********** end account number check **********

mapDoc = os.path.join(filePath, 'radius_report.mxd')
buffer_dist = raw_input('Please input buffer distance in feet') # this is set for feet, if you need a different unit please change the value on line 63 to match the unit

# ********** checking for correctly formatted buffer distance **********
# reference[2]
if buffer_dist.isdigit() == True:
    pass
else:
    buffer_dist = raw_input('Numbers only, please!')
# ********** end distance check **********

arcpy.env.overwriteOutput = True 
arcpy.env.workspace = filePath 

try:

    # ********** begin display creation **********
    # set up sql selection clause for target parcel
    parcelSelection = '"ID" = ' + "'" + idField + "'"
    arcpy.MakeFeatureLayer_management(targetDataset, 'targetDataset', parcelSelection)
    # export layer
    outputFile = idField + '.shp'
    arcpy.CopyFeatures_management('targetDataset', outputFile)

    # ********** begin buffer **********
    # mandatory buffer variables
    in_features = outputFile
    buff_out_fc = idField + '_buffer.shp'
    # see line 26 for buffer_dist variable

    # optional buffer variables
    line_side = ''
    line_end_type = ''
    dissolve_option = ''
    dissolve_field = ''

    # run the buffer
    arcpy.Buffer_analysis(in_features, buff_out_fc, buffer_dist, line_side, line_end_type, dissolve_option, dissolve_field)
    # ********** end buffer **********
    
    # ********** select parcels within buffer zone **********
    # select layer by location, use exported buffer layer & buffer_dist
    arcpy.MakeFeatureLayer_management(targetDataset, 'reportTemp')

    # select layer by attribute variable definition
    in_layer = 'reportTemp'
    sel_type = 'NEW_SELECTION'
    whereClause = parcelSelection
    
    arcpy.SelectLayerByAttribute_management(in_layer, sel_type, whereClause)
    # ********** end select parcels within buffer zone **********
    # selectlayerbylocation variables
    # in_layer is redundant here. if you need to change the variable, do so on line 70
    overlap_type = 'WITHIN_A_DISTANCE'
    select_feat = '' # you may never need to define this variable. from the ArcGIS documentation: "will be selected based on their relationship to the features from this layer or feature class." 
    search_dist = str(buffer_dist) + " Feet" # IF YOU MUST CHANGE THE UNIT, DO NOT DELETE THE SPACE THAT PRECEEDS THE UNIT NAME
    sel_type = 'ADD_TO_SELECTION' # for this program's purpose, ADD_TO_SELECTION will be the only necessary query

    arcpy.SelectLayerByLocation_management(in_layer, overlap_type, select_feat, search_dist, sel_type)
    reportOut = idField + "_selection.shp"
    arcpy.CopyFeatures_management(in_layer, reportOut)
    # ********** end parcel selection **********

    # ********** begin clip operations **********

    # ********** parcels clip **********
    # clip variables
    in_features = reportOut # this is calling the output of the SelectLayerByLocation operation    
    clip_features = buff_out_fc # this is calling the output of the Buffer operation
    clip_out_fc = idField + "_report.shp"
    xy_tolerance = '' # you may never need to define this 

    arcpy.Clip_analysis(in_features, clip_features, clip_out_fc, xy_tolerance)

    # ********** street centerline clip **********
    in_features2 = stCenterline
    #clip_features = buff_out_fc isn't needed as it is redundant
    clip_out_fc2 = idField + "_streets.shp"
    #xy_tolerance = '' this is also unneccesary as it is redundant 
    arcpy.Clip_analysis(in_features2, clip_features, clip_out_fc2, xy_tolerance)
    # ********** end clip operations **********

    # ********** end display creation **********

    # ********** LITERALLY make the display **********
    # create layers, save layers.
    arcpy.MakeFeatureLayer_management(outputFile, 'POI_layer')
    arcpy.SaveToLayerFile_management('POI_layer', 'POI_layer.lyr')

    arcpy.MakeFeatureLayer_management(buff_out_fc, 'buffer_layer')
    arcpy.SaveToLayerFile_management('buffer_layer', 'buffer_layer.lyr')

    arcpy.MakeFeatureLayer_management(clip_out_fc, 'report_layer')
    arcpy.SaveToLayerFile_management('report_layer', 'report_layer.lyr')

    arcpy.MakeFeatureLayer_management(clip_out_fc2, 'centerlines')
    arcpy.SaveToLayerFile_management('centerlines', 'centerlines.lyr')

    # add to map document container
    # don't change the order in which these are added.
    # you will throw off the entire display, unless that's what you want to do.
    mxd = arcpy.mapping.MapDocument(mapDoc)
    df = arcpy.mapping.ListDataFrames(mxd)[0]
    
    addLayer = arcpy.mapping.Layer('POI_layer.lyr')
    arcpy.mapping.AddLayer(df, addLayer, "BOTTOM")

    addLayer = arcpy.mapping.Layer('buffer_layer.lyr')
    arcpy.mapping.AddLayer(df, addLayer, "BOTTOM")

    addLayer = arcpy.mapping.Layer('centerlines.lyr')
    arcpy.mapping.AddLayer(df, addLayer, "BOTTOM")

    addLayer = arcpy.mapping.Layer('report_layer.lyr')
    arcpy.mapping.AddLayer(df, addLayer, "BOTTOM")


    # set extent for display
    # reference[3]
    lyr = arcpy.mapping.ListLayers(mxd, 'buffer_layer', df)[0]
    df.extent = lyr.getExtent(True)
    #arcpy.RefreshActiveView() this came from the example in the reference, not necessary for running straight from pythonwin. 


    # apply template symbology
    layerToUpdate = arcpy.mapping.ListLayers(mxd, 'POI_layer', df)[0]
    arcpy.ApplySymbologyFromLayer_management(layerToUpdate, 'hollow_template.lyr')

    layerToUpdate = arcpy.mapping.ListLayers(mxd, 'buffer_layer', df)[0]
    arcpy.ApplySymbologyFromLayer_management(layerToUpdate, 'hollow_template.lyr')

    layerToUpdate = arcpy.mapping.ListLayers(mxd, 'report_layer', df)[0]
    arcpy.ApplySymbologyFromLayer_management(layerToUpdate, 'report_template.lyr')


    # ********** turn on labelling for R# and street centerlines **********
    # reference[4]
    layer = arcpy.mapping.ListLayers(mxd, '')[2]
    if layer.supports('LABELCLASSES'):
        for lblclass in layer.labelClasses:
            lblclass.showClassLabels = True
    lblclass.expression = '[STREET_NAM]'
    layer.showLabels = True

    layer = arcpy.mapping.ListLayers(mxd, '')[3]
    if layer.supports('LABELCLASSES'):
        for lblclass in layer.labelClasses:
            lblclass.showClassLabels = True
    lblclass.expression = '[ID]'
    layer.showLabels = True

    # the layers that need labels now have them, time to pass them on for export

    # ********** SAVE THE MXD **********
    copyName = idField + "_display.mxd"
    mxd.saveACopy(copyName)
    displayName = copyName
    # ********** SAVED THE MXD **********
    
    # ********** generate the report. this is the most important part  **********
    # ********** the display might be pretty and informative, but this **********
    # ********** is the part the city or county authority needs        **********

    reportLayer = arcpy.mapping.Layer('report_layer.lyr')
    reportTemplate = 'report_template.rlf'

    # ************ EXPORT REPORT TO PDF ************ 
    reportPDF = idField + '_report.pdf'
    arcpy.mapping.ExportReport(reportLayer, reportTemplate, reportPDF)

    # ************ EXPORT DISPLAY TO PDF ************
    outPDF = idField + '_display.pdf'
    arcpy.mapping.ExportToPDF(mxd, outPDF)

    # clean up your mess!
    arcpy.Delete_management(in_features)
    arcpy.Delete_management(copyName)
    arcpy.Delete_management(clip_out_fc)
    arcpy.Delete_management(outputFile)
    arcpy.Delete_management(buff_out_fc)
    arcpy.Delete_management(clip_out_fc2)
    arcpy.Delete_management('POI_layer.lyr')
    arcpy.Delete_management('buffer_layer.lyr')
    arcpy.Delete_management('report_layer.lyr')
    arcpy.Delete_management('centerlines.lyr')
    del mxd, df

except Exception as ex:
    print(ex.args[0])

# 
# references:
#
# 0: General example for sys and os:
# http://www.databaseskill.com/2041443/
#
# 1: How to check if a string starts with a certain prefix:
# http://stackoverflow.com/questions/7539959/python-finding-whether-a-string-starts-with-one-of-a-lists-variable-length-pre
#
# 2: How to check if a variable is an integer:
# http://stackoverflow.com/questions/3501382/checking-whether-a-variable-is-an-integer-or-not
#
# 3: How to set the extent programmatically:
# https://geonet.esri.com/thread/60885
#
# 4: How to turn on labels programmatically:
# http://gis.stackexchange.com/questions/22725/customizing-label-features-using-arcpy
#
