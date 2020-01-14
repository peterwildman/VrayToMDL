# Filename: vraytomdl.py

"""A 3dsmax script to turn vray materials into MDLs"""

import sys
import os

# Import QApplication and the required widgets from PySide2.QtWidgets
from PySide2.QtWidgets import QApplication
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QWidget
from PySide2 import QtWidgets
from PySide2 import QtCore

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QGridLayout
from PySide2.QtWidgets import QLineEdit
from PySide2.QtWidgets import QPushButton
from PySide2.QtWidgets import QHBoxLayout
from PySide2.QtWidgets import QVBoxLayout
from PySide2.QtWidgets import QComboBox
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QDialog
from PySide2.QtWidgets import QDialogButtonBox
from PySide2.QtWidgets import QFormLayout
from PySide2.QtWidgets import QFileDialog

from functools import partial




import MaxPlus
import math
import pymxs
mxs = pymxs.runtime
PARENT = MaxPlus.GetQMaxMainWindow()

texturefolder = "../textures/" 
mdlfolder = "C:/MDL/fake"

class VrayToMDLUI(QtWidgets.QDialog):
    """Vray To MDL View (GUI)."""
    def __init__(self, parent=PARENT):
        super(VrayToMDLUI, self).__init__(parent)

        self.setWindowTitle('Vray to MDL')
        self.setFixedSize(300, 150)
        self.main_layout = QGridLayout()
         # This is the material selector
        self.mat_conversion_options = {"Scene Materials":"scene", "Selected Materials":"selected"}
        self.matComboBox = QComboBox()
        self.matComboBox.addItems(self.mat_conversion_options.keys())
       
        self.matLabel = QLabel("&Materials to Convert:")
        self.matLabel.setBuddy(self.matComboBox)

        topLayout = QHBoxLayout()
        topLayout.addWidget(self.matLabel)
        topLayout.addWidget(self.matComboBox)
        topLayout.addStretch(1)
        # This is adding that mat_conversion_options layout to the top of the layout grid
        self.main_layout.addLayout(topLayout, 0, 0, 1, 3)


        self.mdl_save_location_button = QtWidgets.QPushButton("Save Location for MDLs")
        self.main_layout.addWidget(self.mdl_save_location_button, 2, 0, 1, 3)

           #relative texture path
        self.texture_location_button = QtWidgets.QPushButton("Save Location for Textures")
        self.texture_location_button.setDisabled(True)
        
        self.main_layout.addWidget(self.texture_location_button, 3, 0, 1, 3)

        self.convert_button  = QtWidgets.QPushButton("Convert to MDL")
        self.convert_button.setDisabled(True)
        self.main_layout.addWidget(self.convert_button, 4, 1, 1, 1)
        self.setLayout(self.main_layout)

# Create a Controller class to connect the GUI and the model
class VrayToMDLCtrl:
    """Vray To MDL Controller class."""
    def __init__(self, view, model):
        """Controller initializer."""
        self._model = model
        self._view = view
        # Connect signals and slots
        self._connectSignals()
        # this needs to change
        self.scene_materials = mxs.sceneMaterials

    def _getfile(self, message, button_name):
        dialog = QFileDialog()
        self.basefoldername = dialog.getExistingDirectory()
        button_name.setText(message + self.basefoldername)
        common_prefix = self.basefoldername
        self._view.texture_location_button.setDisabled(False)
        self._model._setmdlpath(self.basefoldername)
       

    def _getrelativefile(self, message, button_name):
        dialog = QFileDialog()
        fname = dialog.getExistingDirectory()
        common_prefix = self.basefoldername
        relative_path = os.path.relpath(fname, common_prefix)
        button_name.setText(message + relative_path)
        self._view.convert_button.setDisabled(False)
        self._model._settexturepath(relative_path)

    def _runtheprogram(self):
        material_list = self._model.getmateriallist(self._view.mat_conversion_options[self._view.matComboBox.currentText()])
        self._model._buildmdls(material_list)
      

    def _connectSignals(self):
        """Connect signals and slots."""
        self.mdlpath = self._view.mdl_save_location_button.clicked.connect(lambda: self._getfile("MDL Save Location: ", self._view.mdl_save_location_button))
        self.texturepath = self._view.texture_location_button.clicked.connect(lambda: self._getrelativefile("Texture Location: ", self._view.texture_location_button))
        self._view.convert_button.clicked.connect(lambda: self._runtheprogram())
class VrayToMDLModel:
    
    
    def __init__(self, texturefolder, mdlfolder):
        """Model initializer."""
        mxs = pymxs.runtime
        self.texturefolder = texturefolder
        self.mdlfolder = mdlfolder
        self.basemdl = "PWOmniPBR_Opacity::PWOmniPBR_Opacity"
        self.mat_dict ={}
        self.rgbmult = 0.003921568
        self.scene_materials = mxs.sceneMaterials

    def _getrgbtofloat(self, rgb):
        return str(round(float(rgb*self.rgbmult ),2))
        
    def _getcolor(self, prop):
        return "color" + "(" +self._getrgbtofloat(prop.r)+","+str(float(prop.g*self.rgbmult ))+","+str(float(prop.b*self.rgbmult ))+")"
        
    def _getiortonormal(self, ior):
        # I am total making this math up , should could back with something better
        return round((ior * .1),2)
        
    def _getselfilltoemmissive(self, selfill):
        #once again, this is just arbrtrary until I can do some tests
        return round((selfill * 40.0),2)
        
    def _getcolortofloat(self, prop):
        return  round(((float(int(prop.r)) + float(int(prop.g)) +float(int(prop.b)))/3)*0.003921568,2)

        
    def _checkfortexture(self, prop):
        #this could be expanded on to check and see if stuff is unchecked or if the value isnt at 100.
        if prop.__class__ != type(None):
            return 1.0
        else:
            return 0.0

    def _gettexture(self, prop):
        if prop.__class__ != type(None):
            options = dir(prop)
            if "filename" in options:
                filename = (str(mxs.filenameFromPath(prop.filename)) , "tex::gamma_srgb")
            elif "HDRIMapName" in options:
                filename = (str(mxs.filenameFromPath(prop.HDRIMapName)) , "tex::gamma_srgb")

            return 'texture_2d("'+(self.texturefolder + filename[0])+'", '+filename[1]+')'
        else:
            return("texture_2d()")

    def _getroughness(self,material):
        if material.brdf_useRoughness == True:
            return round(material.reflection_glossiness, 2)
        else:
            return round((1 -material.reflection_glossiness), 2)
            
    def _getspecnormal(self, material):
        if material.reflection_fresnel == True:
            if material.reflection_lockIOR == True:
                return self._getiortonormal(material.refraction_ior)
            else:
                return self._getiortonormal(material.reflection_ior)
        else:
            return 1.0
            
    def _checkforemmision(self, material):
        if self._checkfortexture(material.texmap_self_illumination) == 1.0:
            return "true"
        else:
            if self._getcolor(material.selfIllumination) != 'color(0.0, 0.0, 0.0)':
                return "true"
            else:
                return "false"
            
            
    def _listprops(self, material):
        #diffuse properties
        self.mat_dict['diffuse_color_constant'] =self._getcolor(material.diffuse)
        self.mat_dict['diffuse_texture'] = self._gettexture(material.texmap_diffuse)
        #reflection properties
        self.mat_dict['reflection_roughness_constant'] = self._getroughness(material)
        self.mat_dict['reflection_roughness_texture_influence'] = self._checkfortexture(material.texmap_reflectionGlossiness)
        self.mat_dict['reflectionroughness_texture'] = self._gettexture(material.texmap_reflectionGlossiness)
        self.mat_dict['specular_constant'] = self._getcolortofloat(material.reflection)
        self.mat_dict['specular_texture_influence'] =self._checkfortexture(material.texmap_reflection)
        self.mat_dict['specular_texture'] = self._gettexture(material.texmap_reflection)
        self.mat_dict['specular_normal'] = self._getspecnormal(material)
        #emmissive properties
        self.mat_dict['emissive_color'] = self._getcolor(material.selfIllumination)
        self.mat_dict['enable_emission'] = self._checkforemmision(material)
        self.mat_dict['emissive_intensity']	=  self._getselfilltoemmissive(material.selfIllumination_multiplier)
        self.mat_dict['emissive_mask_texture'] = self._gettexture(material.texmap_self_illumination)
        return self.mat_dict

    def _makemdl(self, materialname, mat_dict):
            with open(self.mdlfolder +"/"+ materialname +".mdl", "w") as file:
                    file.write("\n")
                    file.write("mdl 1.4;\nimport df::*;\nimport base::*;\nimport math::*;\nimport state::*;\nimport anno::*;\nimport tex::*;\n")
                    file.write("import "+self.basemdl+";\n")
                    file.write("\n\n")
                    file.write("export material "+ materialname + "(*) = "+self.basemdl+"(\n" )
            # all captured info goes inbetween here
                    # Diffuse 
                    file.write("    diffuse_color_constant: ")
                    file.write(mat_dict["diffuse_color_constant"]+",\n")
                    file.write("    diffuse_texture: ")
                    file.write(str(mat_dict["diffuse_texture"])+",\n")
            # Reflection
                    file.write("    reflection_roughness_constant: ")
                    file.write(str(mat_dict["reflection_roughness_constant"])+",\n")
                    file.write("    reflection_roughness_texture_influence: ")
                    file.write(str(mat_dict["reflection_roughness_texture_influence"])+",\n")
                    file.write("    reflectionroughness_texture: ")
                    file.write(str(mat_dict["reflectionroughness_texture"])+",\n")        
                    file.write("    specular_constant: ")
                    file.write(str(mat_dict["specular_constant"])+",\n")        
                    file.write("    specular_texture_influence: ")
                    file.write(str(mat_dict["specular_texture_influence"])+",\n")   
                    file.write("    specular_texture: ")
                    file.write(str(mat_dict["specular_texture"])+",\n")    

                    file.write("    specular_normal: ")
                    file.write(str(mat_dict["specular_normal"])+",\n")  
            #emmissive properties
                    file.write("    emissive_color: ")
                    file.write(str(mat_dict["emissive_color"])+",\n")  
                    file.write("    enable_emission: ")
                    file.write(str(mat_dict["enable_emission"])+",\n")  
                    file.write("    emissive_intensity: ")
                    file.write(str(mat_dict["emissive_intensity"])+",\n")  
                    file.write("    emissive_mask_texture: ")
                    file.write(str(mat_dict["emissive_mask_texture"])+"\n")  # note the lack of comma
                    
            #closeing the file off
                    file.write("\n\n")
                    file.write(");" )
                    file.close        
    def _buildmdls(self, scene_materials):
        for material in scene_materials:
        #print(material)
            if mxs.classof(material) == mxs.VRayMtl:
                
                self._makemdl(str(material.name),self._listprops(material))
            elif mxs.classof(material) == mxs.Multimaterial:
                #print("multie")
                for submaterial in material:
                    if mxs.classof(submaterial) == mxs.VRayMtl:
                        self._makemdl(str(submaterial.name),self._listprops(submaterial))
            else:
                print("Unsupported material" + str( material ))
    
    def getmateriallist(self, scene_or_selected):
        material_list = []
        if scene_or_selected == "selected":
            if len(mxs.selection) >= 1:
                for objects in mxs.selection:
                    if objects.material  not in material_list:
                        material_list.append(objects.material)
                else:
                    pass
        elif scene_or_selected == "scene":
            material_list = mxs.sceneMaterials
        return material_list
    
    def _setmdlpath(self, mdlpath):
        self.mdlfolder = mdlpath
        print(self.mdlfolder) 

    def _settexturepath(self, texturepath):
        texturepath = texturepath.replace("\\","/")
        self.texturefolder = texturepath + "/"
        print(self.texturefolder)

# Main Loop
def main():
    try:
        view.close()
    except:
        pass
    view = VrayToMDLUI()
    view.show()
    model = VrayToMDLModel(texturefolder=texturefolder,mdlfolder=mdlfolder)
    VrayToMDLCtrl(view=view, model=model)



if __name__ == '__main__':
    main()
   