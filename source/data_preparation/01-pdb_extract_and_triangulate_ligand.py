#!/usr/bin/python
import numpy as np
import os, shutil
import Bio
import shutil
from Bio.PDB import * 
import sys
import importlib
from IPython.core.debugger import set_trace

# Local includes
from default_config.masif_opts import masif_opts
from triangulation.computeMSMS import computeMSMS
from triangulation.fixmesh import fix_mesh
import pymesh
from input_output.extractPDB import extractPDB
from input_output.save_ply import save_ply
from input_output.read_ply import read_ply
from input_output.protonate import protonate
from triangulation.computeHydrophobicity import computeHydrophobicity
from triangulation.computeCharges import computeCharges, assignChargesToNewMesh
from triangulation.computeAPBS import computeAPBS
from triangulation.compute_normal import compute_normal
from sklearn.neighbors import KDTree

if len(sys.argv) <= 1: 
    print("Usage: {config} "+sys.argv[0]+" PDBID_ligand")
    sys.exit(1)


# Save the chains as separate files. 
pdb_id = sys.argv[1]
sdf_filename = os.path.join(masif_opts["ligand"]["assembly_dir"],pdb_id+".sdf")
pdb_filename = os.path.join(masif_opts["ligand"]["assembly_dir"],pdb_id+".pdb")

tmp_dir= masif_opts['tmp_dir']
outBase = tmp_dir+"/"+pdb_id
shutil.copy(pdb_filename, outBase+'.pdb')

# Compute MSMS of surface w/hydrogens,
try:
    vertices1, faces1, normals1, names1, areas1 = computeMSMS(sdf_filename,\
        protonate=True, isLigand=True)
except:
    set_trace()

#TODO: Check how can this work for ligands
# Compute "charged" vertices
#if masif_opts['use_hbond']:
    #vertex_hbond = computeCharges(outBase, vertices1, names1)

# For each surface residue, assign the hydrophobicity of its amino acid. 
#if masif_opts['use_hphob']:
 #   vertex_hphobicity = computeHydrophobicity(names1)

# If protonate = false, recompute MSMS of surface, but without hydrogens (set radius of hydrogens to 0).
vertices2 = vertices1
faces2 = faces1

# Fix the mesh.
mesh = pymesh.form_mesh(vertices2, faces2)
regular_mesh = fix_mesh(mesh, masif_opts['mesh_res'])

# Compute the normals
vertex_normal = compute_normal(regular_mesh.vertices, regular_mesh.faces)
# Assign charges on new vertices based on charges of old vertices (nearest
# neighbor)

#if masif_opts['use_hbond']:
 #   vertex_hbond = assignChargesToNewMesh(regular_mesh.vertices, vertices1,\
  #      vertex_hbond, masif_opts)

#if masif_opts['use_hphob']:
 #   vertex_hphobicity = assignChargesToNewMesh(regular_mesh.vertices, vertices1,\
  #      vertex_hphobicity, masif_opts)

#if masif_opts['use_apbs']:
 #   vertex_charges = computeAPBS(regular_mesh.vertices, outBase+'.pdb', outBase)

iface = np.zeros(len(regular_mesh.vertices))
if 'compute_iface' in masif_opts and masif_opts['compute_iface'] and False:
    # Compute the surface of the entire complex and from that compute the interface.
    v3, f3, _, _, _ = computeMSMS(pdb_filename,\
        protonate=True)
    # Regularize the mesh
    mesh = pymesh.form_mesh(v3, f3)
    # I believe It is not necessary to regularize the full mesh. This can speed up things by a lot.
    full_regular_mesh = mesh
    # Find the vertices that are in the iface.
    v3 = full_regular_mesh.vertices
    # Find the distance between every vertex in regular_mesh.vertices and those in the full complex.
    kdt = KDTree(v3)
    d, r = kdt.query(regular_mesh.vertices)
    d = np.square(d) # Square d, because this is how it was in the pyflann version.
    assert(len(d) == len(regular_mesh.vertices))
    iface_v = np.where(d >= 2.0)[0]
    iface[iface_v] = 1.0
    # Convert to ply and save.
    save_ply(out_filename1+".ply", regular_mesh.vertices,\
                        regular_mesh.faces, normals=vertex_normal, charges=vertex_charges,\
                        normalize_charges=True, hbond=vertex_hbond, hphob=vertex_hphobicity,\
                        iface=iface)

else:
    # Convert to ply and save.
    save_ply(outBase+".ply", regular_mesh.vertices,\
                        regular_mesh.faces, normals=vertex_normal)#, charges=vertex_charges,\
                        #normalize_charges=True, hbond=vertex_hbond, hphob=vertex_hphobicity)
if not os.path.exists(masif_opts['ply_chain_dir']):
    os.makedirs(masif_opts['ply_chain_dir'])
if not os.path.exists(masif_opts['pdb_chain_dir']):
    os.makedirs(masif_opts['pdb_chain_dir'])
shutil.copy(outBase+'.ply', masif_opts['ply_chain_dir'])
shutil.copy(outBase+'.pdb', masif_opts['pdb_chain_dir'])