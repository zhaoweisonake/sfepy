#!/usr/bin/env python
"""
Convert a mesh file from one SfePy-supported format to another.

Examples::

  $ ./script/convert_mesh.py meshes/3d/cylinder.mesh new.vtk
  $ ./script/convert_mesh.py meshes/3d/cylinder.mesh new.vtk -s2.5
  $ ./script/convert_mesh.py meshes/3d/cylinder.mesh new.vtk -s0.5,2,1
  $ ./script/convert_mesh.py meshes/3d/cylinder.mesh new.vtk -s0.5,2,1 -c 0
"""
from __future__ import absolute_import
import sys
from six.moves import range
sys.path.append('.')

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from sfepy.base.base import nm, output
from sfepy.discrete.fem import Mesh, FEDomain
from sfepy.discrete.fem.meshio import (output_mesh_formats, MeshIO,
                                       supported_cell_types)

helps = {
    'scale' : 'scale factor (float or comma-separated list for each axis)'
    ' [default: %(default)s]',
    'center' : 'center of the output mesh (0 for origin or'
    ' comma-separated list for each axis) applied after scaling'
    ' [default: %(default)s]',
    'refine' : 'uniform refinement level [default: %(default)s]',
    'format' : 'output mesh format (overrides filename_out extension)',
    'list' : 'list supported readable/writable output mesh formats',
}

def _parse_val_or_vec(option, name, parser):
    if option is not None:
        try:
            try:
                option = float(option)
            except ValueError:
                option = [float(ii) for ii in option.split(',')]
            option = nm.array(option, dtype=nm.float64, ndmin=1)
        except:
            output('bad %s! (%s)' % (name, option))
            parser.print_help()
            sys.exit(1)

    return option

def main():
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('-s', '--scale', metavar='scale',
                        action='store', dest='scale',
                        default=None, help=helps['scale'])
    parser.add_argument('-c', '--center', metavar='center',
                        action='store', dest='center',
                        default=None, help=helps['center'])
    parser.add_argument('-r', '--refine', metavar='level',
                        action='store', type=int, dest='refine',
                        default=0, help=helps['refine'])
    parser.add_argument('-f', '--format', metavar='format',
                        action='store', type=str, dest='format',
                        default=None, help=helps['format'])
    parser.add_argument('-l', '--list', action='store_true',
                        dest='list', help=helps['list'])
    parser.add_argument('filename_in')
    parser.add_argument('filename_out')
    options = parser.parse_args()

    if options.list:
        output('Supported readable mesh formats:')
        output('--------------------------------')
        output_mesh_formats('r')
        output('')
        output('Supported writable mesh formats:')
        output('--------------------------------')
        output_mesh_formats('w')
        sys.exit(0)

    scale = _parse_val_or_vec(options.scale, 'scale', parser)
    center = _parse_val_or_vec(options.center, 'center', parser)

    filename_in = options.filename_in
    filename_out = options.filename_out

    mesh = Mesh.from_file(filename_in)

    if scale is not None:
        if len(scale) == 1:
            tr = nm.eye(mesh.dim, dtype=nm.float64) * scale
        elif len(scale) == mesh.dim:
            tr = nm.diag(scale)
        else:
            raise ValueError('bad scale! (%s)' % scale)
        mesh.transform_coors(tr)

    if center is not None:
        cc = 0.5 * mesh.get_bounding_box().sum(0)
        shift = center - cc
        tr = nm.c_[nm.eye(mesh.dim, dtype=nm.float64), shift[:, None]]
        mesh.transform_coors(tr)

    if options.refine > 0:
        domain = FEDomain(mesh.name, mesh)
        output('initial mesh: %d nodes %d elements'
               % (domain.shape.n_nod, domain.shape.n_el))

        for ii in range(options.refine):
            output('refine %d...' % ii)
            domain = domain.refine()
            output('... %d nodes %d elements'
                   % (domain.shape.n_nod, domain.shape.n_el))

        mesh = domain.mesh

    io = MeshIO.for_format(filename_out, format=options.format,
                           writable=True)

    cell_types = ', '.join(supported_cell_types[io.format])
    output('writing [%s] %s...' % (cell_types, filename_out))
    mesh.write(filename_out, io=io)
    output('...done')

if __name__ == '__main__':
    main()
