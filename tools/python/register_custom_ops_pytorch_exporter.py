# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
#
# Register pytorch symbolic for export using ONNX Runtime contrib ops

from torch.onnx import register_custom_op_symbolic
from torch.onnx.symbolic_helper import parse_args


_onnx_opset_version = 1


def register_custom_op(is_ortmodule=False):
    """
    This function registers symbolic functions for
    custom ops that are implemented as part of ONNX Runtime
    """

    # Symbolic definition
    def inverse(g, self):
        return g.op("com.microsoft::Inverse", self)

    def gelu(g, self):
        return g.op("com.microsoft::Gelu", self)

    def triu(g, self, diagonal):
        return g.op("com.microsoft::Trilu", self, diagonal, upper_i=1)

    def tril(g, self, diagonal):
        return g.op("com.microsoft::Trilu", self, diagonal, upper_i=0)

    # Op Registration
    register_custom_op_symbolic('::inverse', inverse, _onnx_opset_version)
    register_custom_op_symbolic('::gelu', gelu, _onnx_opset_version)
    register_custom_op_symbolic('::triu', triu, _onnx_opset_version)
    register_custom_op_symbolic('::tril', tril, _onnx_opset_version)

    if is_ortmodule:
        @parse_args('v', 'v', 'i', 'b', 'b')
        def embedding(g, weight, indices, padding_idx, scale_grad_by_freq, sparse):
            custom_attributes_json = (
                '{'
                f'"padding_idx":{str(padding_idx)},'
                f'"scale_grad_by_freq":{str(scale_grad_by_freq).lower()},'
                f'"sparse":{str(sparse).lower()}'
                '}'
            )
            return g.op("com.microsoft::ATenOp", weight, indices, name_s='aten::embedding',
                        custom_attributes_json_s=custom_attributes_json)

        register_custom_op_symbolic('::embedding', embedding, _onnx_opset_version)

        @parse_args('v', 'is', 'is', 'is', 'is', 'b')
        def max_pool2d(g, self, kernel_size, stride, padding, dilation, ceil_mode):
            custom_attributes_json = (
                '{'
                f'"kernel_size":{str(kernel_size)},'
                f'"stride":{str(stride)},'
                f'"padding":{str(padding)},'
                f'"dilation":{str(dilation)},'
                f'"ceil_mode":{str(ceil_mode).lower()}'
                '}'
            )
            return g.op("com.microsoft::ATenOp", self, name_s='aten::max_pool2d_with_indices',
                        custom_attributes_json_s=custom_attributes_json, outputs=2)[0]

        register_custom_op_symbolic('::max_pool2d', max_pool2d, _onnx_opset_version)

        @parse_args('v', 'i', 'i', 'i')
        def unfold(g, input, dimension, size, step):
            custom_attributes_json = (
                '{'
                f'"dimension":{str(dimension)},'
                f'"size":{str(size)},'
                f'"step":{str(step)}'
                '}'
            )
            return g.op("com.microsoft::ATenOp", input, name_s='aten::unfold',
                        custom_attributes_json_s=custom_attributes_json)

        register_custom_op_symbolic('::unfold', unfold, _onnx_opset_version)


def unregister_custom_op():
    """
    This function unregisters symbolic functions for
    custom ops that are implemented as part of ONNX Runtime
    """

    import torch.onnx.symbolic_registry as sym_registry

    # TODO: replace this once PyTorch supports unregister natively.
    def unregister(name, opset_version):
        ns, kind = name.split("::")
        from torch.onnx.symbolic_helper import _onnx_stable_opsets

        for version in _onnx_stable_opsets:
            if version >= opset_version and sym_registry.is_registered_op(kind, ns, version):
                del sym_registry._registry[(ns, version)][kind]

    unregister('::inverse', _onnx_opset_version)
    unregister('::gelu', _onnx_opset_version)
    unregister('::triu', _onnx_opset_version)
    unregister('::tril', _onnx_opset_version)