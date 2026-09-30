import xml
import xml.etree
import xml.etree.ElementTree as ET

import locale

import argparse
import os

def makeelementwtext(elname, text):
    elret = ET.Element(elname)
    elret.text = text
    return elret

def cmakelist_getfunctioncallings(cmakecontent : str):
    getting_args = False
    currentfunc = ""
    currentfuncargs = []

    function_callings = []

    for line in cmakecontent.splitlines():
        if line.count("(") != 0:
            getting_args = True
            currentfunc = line[:line.find("(")]
        
        if getting_args == True:
            if line.count(")"):
                currentfuncargs += line[line.find("(")+1:line.find(")")].split()
            else:
                currentfuncargs += line[line.find("(")+1:].split()

        #do stuff

        if line.count(")") != 0:
            getting_args = False
            function_callings.append({"funcname":currentfunc, "funcargs":currentfuncargs})
            currentfuncargs = []

    return function_callings

        



def makeconfig(plat : str, type : str, 
               incdirs : str, libdirs : str, 
               libs : str, defines : str,
               configtype : str):
    return {"gendebuginfo":1 if type.count("Debug")!=0 else 0, 
            "additlibdirs":libdirs, 
            "additlibs":libs, 
            "subsystem":"Console", 
            
            "warninglevel":"1",
            "defines":defines,
            "includes":incdirs,
            
            "outdir":"./projdir",
            "intdir":"./intdir",
            
            "name":f"{type}|{plat}", 
            "type":type, 
            "platform":plat,
            "configtype":configtype
            }


#returns a list: [{.vcxproj and .vcxproj.filters}]
def converter_to_vcxproj(cmakelist_filepath : str, autofilter):
    with open(cmakelist_filepath) as f:
        cmake_filelines = f.read()

    targets = []
    incdirs = []
    libdirs = []



    for functioncall in cmakelist_getfunctioncallings(cmake_filelines):
        args = functioncall["funcargs"]
        if functioncall["funcname"] == "add_executable":
            targets.append({"name":args[0], "type":"Application",    "sourcefiles":args[1:], "libfiles":[]})
        elif functioncall["funcname"] == "add_library":

            if args[1] == "SHARED":     targets.append({"name":args[0], "type":"DynamicLibrary", "sourcefiles":args[2:], "libfiles":[]})
            elif args[1] == "STATIC":   targets.append({"name":args[0], "type":"StaticLibrary", "sourcefiles":args[2:], "libfiles":[]})
            elif args[1] == "MODULE":   targets.append({"name":args[0], "type":"DynamicLibrary", "sourcefiles":args[2:], "libfiles":[]}) #idk
            else:                       targets.append({"name":args[0], "type":"StaticLibrary", "sourcefiles":args[1:], "libfiles":[]})
        elif functioncall["funcname"] == "include_directories":
            for dir in args:
                incdirs.append(dir)
        elif functioncall["funcname"] == "link_directories":
            for dir in args:
                libdirs.append(dir)
        elif functioncall["funcname"] == "target_link_libraries":
            for i in range(len(targets)):
                if targets[i]["name"] != args[0]:continue
                for j in range(len(args[1:])): args[j+1] += ";"
                targets[i]["libfiles"] = args[1:]

    vcxprojfiles = []

    for i in range(len(incdirs)): incdirs[i] += ";"
    for i in range(len(libdirs)): libdirs[i] += ";"

    for target in targets:
        vcxprojfiles.append(make_vcxproj(target, autofilter, "".join(incdirs), "".join(libdirs)))

    return vcxprojfiles




        

def make_vcxproj(target, autofilter, incdirs, libdirs):
    vcxproj_entry = ET.Element("Project", {   "DefaultTargets": "Build", "xmlns":"http://schemas.microsoft.com/developer/msbuild/2003"   } )
    vcxproj_projconfigs = ET.Element("ItemGroup", {"Label":"ProjectConfigurations"})
    vcxproj_globals = ET.Element("PropertyGroup", {"Label":"Globals"})
    vcxproj_compileitems = ET.Element("ItemGroup")
    vcxproj_includeitems = ET.Element("ItemGroup")
    
    vcxproj_filters = ET.Element("Project", { "ToolsVersion": "4.0", "xmlns":"http://schemas.microsoft.com/developer/msbuild/2003"  })
    vcxproj_declarefilters = ET.Element("ItemGroup")
    vcxproj_declaresources = ET.Element("ItemGroup")
    vcxproj_declareheaders = ET.Element("ItemGroup")
    
    configs = [] #name, type, platform


    configs.append(makeconfig("x64",    "Debug",    incdirs, libdirs, "".join(target["libfiles"]), "", target["type"]))
    configs.append(makeconfig("Win32",  "Debug",    incdirs, libdirs, "".join(target["libfiles"]), "", target["type"]))
    configs.append(makeconfig("x64",    "Release",  incdirs, libdirs, "".join(target["libfiles"]), "", target["type"]))
    configs.append(makeconfig("Win32",  "Release",  incdirs, libdirs, "".join(target["libfiles"]), "", target["type"]))
    
    
    vcxproj_entry.append(vcxproj_projconfigs)
    vcxproj_entry.append(vcxproj_globals)
    vcxproj_entry.append(ET.Element("Import", {"Project":"$(VCTargetsPath)\\Microsoft.Cpp.Default.props"}))
    for entry in configs:
        propertygroupconfig = ET.Element("PropertyGroup", 
                                         {"Condition":f"'$(Configuration)|$(Platform)'=='{entry["name"]}'",
                                          "Label":"Configuration"})
        propertygroupconfig.append(makeelementwtext("ConfigurationType", entry["configtype"]))
        propertygroupconfig.append(makeelementwtext("UseDebugLibraries", "true" if entry["type"]=="Debug" else "false"))
        propertygroupconfig.append(makeelementwtext("PlatformToolset", "v143"))
        propertygroupconfig.append(makeelementwtext("CharacterSet", "NotSet"))
        vcxproj_entry.append(propertygroupconfig)
        
    vcxproj_entry.append(ET.Element("Import", {"Project":"$(VCTargetsPath)\\Microsoft.Cpp.props"}))
    vcxproj_entry.append(ET.Element("ImportGroup", {"Label":"ExtensionSettings"}))
    vcxproj_entry.append(ET.Element("ImportGroup", {"Label":"Shared"}))
    for entry in configs:
        propertysheets = ET.Element("ImportGroup", 
                                         {"Label":"PropertySheets",
                                          "Condition":f"'$(Configuration)|$(Platform)'=='{entry["name"]}'"})
        propertysheets.append(ET.Element("Import", 
                                         {"Project":"$(UserRootDir)\\Microsoft.Cpp.$(Platform).user.props",
                                          "Condition":"exists('$(UserRootDir)\\Microsoft.Cpp.$(Platform).user.props')",
                                          "Label":"LocalAppDataPlatform"}))
        vcxproj_entry.append(propertysheets)
    vcxproj_entry.append(ET.Element("PropertyGroup", {"Label":"UserMacros"}))
    propertygroupdirsettings = ET.Element("PropertyGroup", 
                                 {"Condition":f"'$(Configuration)|$(Platform)'=='{configs[0]["name"]}'"})
    propertygroupdirsettings.append(makeelementwtext("OutDir", configs[0]["outdir"]))
    propertygroupdirsettings.append(makeelementwtext("IntDir", configs[0]["intdir"]))
    vcxproj_entry.append(propertygroupdirsettings)
    
    for entry in configs:
        itemdefgroup = ET.Element("ItemDefinitionGroup", 
                                         {"Condition":f"'$(Configuration)|$(Platform)'=='{entry["name"]}'"})
        clcompile = ET.Element("ClCompile")
        link = ET.Element("Link")
        itemdefgroup.append(clcompile)
        itemdefgroup.append(link)
        vcxproj_entry.append(itemdefgroup)
    
        clcompile.append(makeelementwtext("WarningLevel", f"Level{entry["warninglevel"]}"))
        clcompile.append(makeelementwtext("SDLCheck", "false"))
        clcompile.append(makeelementwtext("PreprocessorDefinitions", entry["defines"]))
        clcompile.append(makeelementwtext("AdditionalIncludeDirectories", entry["includes"]))
        clcompile.append(makeelementwtext("LanguageStandard", "stdcpp17"))
        clcompile.append(makeelementwtext("MultiProcessorCompilation", "true"))
        clcompile.append(makeelementwtext("FunctionLevelLinking", "true" if entry["gendebuginfo"]==1 else "false"))
    
        link.append(makeelementwtext("SubSystem", entry["subsystem"]))
        link.append(makeelementwtext("GenerateDebugInformation", "true" if entry["gendebuginfo"]==1 else "false"))
        link.append(makeelementwtext("AdditionalLibraryDirectories", entry["additlibdirs"]))
        link.append(makeelementwtext("AdditionalDependencies", entry["additlibs"]))
    
    
    vcxproj_entry.append(vcxproj_compileitems)
    vcxproj_entry.append(vcxproj_includeitems)
    
    vcxproj_entry.append(ET.Element("Import", {"Project":"$(VCTargetsPath)\\Microsoft.Cpp.targets"}))
    vcxproj_entry.append(ET.Element("ImportGroup", {"Label":"ExtensionTargets"}))
    
    vcxproj_filters.append(vcxproj_declarefilters)
    vcxproj_filters.append(vcxproj_declaresources)
    vcxproj_filters.append(vcxproj_declareheaders)
    
    ###
    #end
    ###
    
    vcxproj_globals.append(makeelementwtext("VCProjectVersion", "17.0"))
    
    for entry in configs:
        projconfig = ET.Element("ProjectConfiguration", {"Include": entry["name"]})
        projconfig.append(makeelementwtext("Configuration", entry["type"]))
        projconfig.append(makeelementwtext("Platform", entry["platform"]))
    
        vcxproj_projconfigs.append(projconfig)
    
    for file in target["sourcefiles"]:
        vcxproj_compileitems.append(ET.Element("ClCompile", {"Include": file}))
        if autofilter != None:
            for i in range(len(file)):
                if file[i] == "\\": file[i] = "/"
            dirpath = file[:file.rfind("/")]
            if vcxproj_declarefilters.find(dirpath) == None:
                vcxproj_declarefilters.append(ET.Element("Filter", {"Include":dirpath}))
            
            sourcefilefilter = ET.Element("ClCompile", {"Include": file})
            sourcefilefilter.append(makeelementwtext("Filter", dirpath))
            vcxproj_declaresources.append(sourcefilefilter)
    
    ET.indent(vcxproj_entry)
    ET.indent(vcxproj_filters)
    
    
    #main proj
    vcxprojbuffer = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
    vcxprojbuffer += ET.tostring(vcxproj_entry).decode()
    
    #filters
    vcxprojfilterbuffer = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
    vcxprojfilterbuffer += ET.tostring(vcxproj_filters).decode()

    return {"name":target["name"], "projbuffer":vcxprojbuffer, "projfilterbuffer":vcxprojfilterbuffer}