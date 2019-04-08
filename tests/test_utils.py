import pytest
import torch

from maml.modules import MetaLinear
from maml.utils import update_parameters

@pytest.fixture
def model():
    model = MetaLinear(3, 1, bias=False)
    model.weight.data = torch.tensor([[2., 3., 5.]])
    return model

def test_update_parameters(model):
    """
    The loss function (with respect to the weights of the model w) is defined as
        f(w) = 0.5 * (1 * w_1 + 2 * w_2 + 3 * w_3) ** 2
    with w = [2, 3, 5].

    The gradient of the function f with respect to w, and evaluated
    on w = [2, 3, 5], is:
        df / dw_1 = 1 * (1 * w_1 + 2 * w_2 + 3 * w_3) = 23
        df / dw_2 = 2 * (1 * w_1 + 2 * w_2 + 3 * w_3) = 46
        df / dw_3 = 3 * (1 * w_1 + 2 * w_2 + 3 * w_3) = 69

    The updated parameter w' is then given by one step of gradient descent,
    with step size 0.5:
        w'_1 = w_1 - 0.5 * df / dw_1 = 2 - 0.5 * 23 = -9.5
        w'_2 = w_2 - 0.5 * df / dw_2 = 3 - 0.5 * 46 = -20
        w'_3 = w_3 - 0.5 * df / dw_3 = 5 - 0.5 * 68 = -29.5
    """
    train_inputs = torch.tensor([[1., 2., 3.]])
    train_loss = 0.5 * (model(train_inputs) ** 2)

    params = update_parameters(model, train_loss, params=None,
        step_size=0.5, first_order=False)

    assert train_loss.item() == 264.5
    assert list(params.keys()) == ['weight']
    assert torch.all(params['weight'].data == torch.tensor([[-9.5, -20., -29.5]]))

    """
    The new loss function (still with respect to the weights of the model w) is
    defined as:
        g(w) = 0.5 * (4 * w'_1 + 5 * w'_2 + 6 * w'_3) ** 2
             = 0.5 * (4 * (w_1 - 0.5 * df / dw_1)
                    + 5 * (w_2 - 0.5 * df / dw_2)
                    + 6 * (w_3 - 0.5 * df / dw_3)) ** 2
             = 0.5 * (4 * (w_1 - 0.5 * 1 * (1 * w_1 + 2 * w_2 + 3 * w_3))
                    + 5 * (w_2 - 0.5 * 2 * (1 * w_1 + 2 * w_2 + 3 * w_3))
                    + 6 * (w_3 - 0.5 * 3 * (1 * w_1 + 2 * w_2 + 3 * w_3))) ** 2
             = 0.5 * ((4 - 4 * 0.5 - 5 * 1.0 - 6 * 1.5) * w_1
                    + (5 - 4 * 1.0 - 5 * 2.0 - 6 * 3.0) * w_2
                    + (6 - 4 * 1.5 - 5 * 3.0 - 6 * 4.5) * w_3) ** 2
             = 0.5 * (-12 * w_1 - 27 * w_2 - 42 * w_3) ** 2

    Therefore the gradient of the function g with respect to w (and evaluated
    on w = [2, 3, 5]) is:
        dg / dw_1 = -12 * (-12 * w_1 - 27 * w_2 - 42 * w_3) =  3780
        dg / dw_2 = -27 * (-12 * w_1 - 27 * w_2 - 42 * w_3) =  8505
        dg / dw_3 = -42 * (-12 * w_1 - 27 * w_2 - 42 * w_3) = 13230
    """
    test_inputs = torch.tensor([[4., 5., 6.]])
    test_loss = 0.5 * (model(test_inputs, params=params) ** 2)

    grads = torch.autograd.grad(test_loss, model.parameters())

    assert test_loss.item() == 49612.5
    assert len(grads) == 1
    assert torch.all(grads[0].data == torch.tensor([[3780., 8505., 13230.]]))

def test_update_parameters_first_order(model):
    """
    The loss function (with respect to the weights of the model w) is defined as
        f(w) = 0.5 * (4 * w_1 + 5 * w_2 + 6 * w_3) ** 2
    with w = [2, 3, 5].

    The gradient of the function f with respect to w, and evaluated
    on w = [2, 3, 5] is:
        df / dw_1 = 4 * (4 * w_1 + 5 * w_2 + 6 * w_3) = 212
        df / dw_2 = 5 * (4 * w_1 + 5 * w_2 + 6 * w_3) = 265
        df / dw_3 = 6 * (4 * w_1 + 5 * w_2 + 6 * w_3) = 318

    The updated parameter w' is then given by one step of gradient descent,
    with step size 0.5:
        w'_1 = w_1 - 0.5 * df / dw_1 = 2 - 0.5 *  9744 = -104
        w'_2 = w_2 - 0.5 * df / dw_2 = 3 - 0.5 * 10416 = -129.5
        w'_3 = w_3 - 0.5 * df / dw_3 = 5 - 0.5 * 12432 = -154
    """
    train_inputs = torch.tensor([[4., 5., 6.]])
    train_loss = 0.5 * (model(train_inputs) ** 2)

    params = update_parameters(model, train_loss, params=None,
        step_size=0.5, first_order=True)

    assert train_loss.item() == 1404.5
    assert list(params.keys()) == ['weight']
    assert torch.all(params['weight'].data == torch.tensor([[-104., -129.5, -154.]]))

    """
    The new loss function (still with respect to the weights of the model w) is
    defined as:
        g(w) = 0.5 * (1 * w'_1 + 2 * w'_2 + 3 * w'_3) ** 2

    Since we computed w' with the first order approximation, the gradient of the
    function g with respect to w, and evaluated on w = [2, 3, 5], is:
        dg / dw_1 = 1 * (1 * w'_1 + 2 * w'_2 + 3 * w'_3) =  -825
        dg / dw_2 = 2 * (1 * w'_1 + 2 * w'_2 + 3 * w'_3) = -1650
        dg / dw_3 = 3 * (1 * w'_1 + 2 * w'_2 + 3 * w'_3) = -2475
    """
    test_inputs = torch.tensor([[1., 2., 3.]])
    test_loss = 0.5 * (model(test_inputs, params=params) ** 2)

    grads = torch.autograd.grad(test_loss, model.parameters())

    assert test_loss.item() == 340312.5
    assert len(grads) == 1
    assert torch.all(grads[0].data == torch.tensor([[-825., -1650., -2475.]]))

def test_multiple_update_parameters(model):
    """
    The loss function (with respect to the weights of the model w) is defined as
        f(w) = 0.5 * (1 * w_1 + 2 * w_2 + 3 * w_3) ** 2
    with w = [2, 3, 5].

    The gradient of f with respect to w is:
        df / dw_1 = 1 * (1 * w_1 + 2 * w_2 + 3 * w_3) = 23
        df / dw_2 = 2 * (1 * w_1 + 2 * w_2 + 3 * w_3) = 46
        df / dw_3 = 3 * (1 * w_1 + 2 * w_2 + 3 * w_3) = 69

    The updated parameters are given by:
        w'_1 = w_1 - 1. * df / dw_1 = 2 - 1. * 23 = -21
        w'_2 = w_2 - 1. * df / dw_2 = 3 - 1. * 46 = -43
        w'_3 = w_3 - 1. * df / dw_3 = 5 - 1. * 69 = -64
    """
    train_inputs = torch.tensor([[1., 2., 3.]])

    train_loss_1 = 0.5 * (model(train_inputs) ** 2)
    params_1 = update_parameters(model, train_loss_1, params=None,
        step_size=1., first_order=False)

    assert train_loss_1.item() == 264.5
    assert list(params_1.keys()) == ['weight']
    assert torch.all(params_1['weight'].data == torch.tensor([[-21., -43., -64.]]))

    """
    The new loss function is defined as
        g(w) = 0.5 * (1 * w'_1 + 2 * w'_2 + 3 * w'_3) ** 2
    with w = [2, 3, 5].

    The gradient of g with respect to w is:
        dg / dw_1 = (1 * dw'_1 / dw_1 + 2 * dw'_2 / dw_1 + 3 * dw'_3 / dw_1)
                        * (1 * w'_1 + 2 * w'_2 + 3 * w'_3)
                  = (1 * (1 - 1. * 1 * 1) + 2 * (-1. * 2 * 1) + 3 * (-1. * 3 * 1))
                        * (1 * w'_1 + 2 * w'_2 + 3 * w'_3)
                  = 3887
        dg / dw_2 = (1 * dw'_1 / dw_2 + 2 * dw'_2 / dw_2 + 3 * dw'_3 / dw_2)
                        * (1 * w'_1 + 2 * w'_2 + 3 * w'_3)
                  = (1 * (-1. * 1 * 2) + 2 * (1 - 1. * 2 * 2) + 3 * (-1. * 3 * 2))
                        * (1 * w'_1 + 2 * w'_2 + 3 * w'_3)
                  = 7774
        dg / dw_3 = (1 * dw'_1 / dw_3 + 2 * dw'_2 / dw_3 + 3 * dw'_3 / dw_3)
                        * (1 * w'_1 + 2 * w'_2 + 3 * w'_3)
                  = (1 * (-1. * 1 * 3) + 2 * (-1. * 2 * 3) + 3 * (1 - 1. * 3 * 3))
                  = 11661

    The updated parameters are given by:
        w''_1 = w'_1 - 1. * dg / dw_1 = -21 - 1. *  3887 =  -3908
        w''_2 = w'_2 - 1. * dg / dw_2 = -43 - 1. *  7774 =  -7817
        w''_3 = w'_3 - 1. * dg / dw_3 = -64 - 1. * 11661 = -11725
    """
    train_loss_2 = 0.5 * (model(train_inputs, params=params_1) ** 2)
    params_2 = update_parameters(model, train_loss_2, params=params_1,
        step_size=1., first_order=False)

    assert train_loss_2.item() == 44700.5
    assert list(params_2.keys()) == ['weight']
    assert torch.all(params_2['weight'].data == torch.tensor([[-3908., -7817., -11725.]]))

    """
    The new loss function is defined as
        h(w) = 1 * w''_1 + 2 * w''_2 + 3 * w''_3
    with w = [2, 3, 5].

    The gradient of h with respect to w is:
        dh / dw_1 = 1 * dw''_1 / dw_1 + 2 * dw''_2 / dw_1 + 3 * dw''_3 / dw_1
                  = ... = -2379
        dh / dw_2 = 1 * dw''_1 / dw_2 + 2 * dw''_2 / dw_2 + 3 * dw''_3 / dw_2
                  = ... = -4758
        dh / dw_3 = 1 * dw''_1 / dw_3 + 2 * dw''_2 / dw_3 + 3 * dw''_3 / dw_3
                  = ... = -7137

    The updated parameters are given by:
        w'''_1 = w''_1 - 1. * dh / dw_1 =  -3908 - 1. * -2379 = -1529
        w'''_2 = w''_2 - 1. * dh / dw_2 =  -7817 - 1. * -4758 = -3059
        w'''_3 = w''_3 - 1. * dh / dw_3 = -11725 - 1. * -7137 = -4588
    """
    train_loss_3 = model(train_inputs, params=params_2)
    params_3 = update_parameters(model, train_loss_3, params=params_2,
        step_size=1., first_order=False)

    assert train_loss_3.item() == -54717.
    assert list(params_3.keys()) == ['weight']
    assert torch.all(params_3['weight'].data == torch.tensor([[-1529., -3059., -4588.]]))

    """
    The new loss function is defined as
        l(w) = 4 * w'''_1 + 5 * w'''_2 + 6 * w'''_3
    with w = [2, 3, 5].

    The gradient of l with respect to w is:
        dl / dw_1 = 4 * dw'''_1 / dw_1 + 5 * dw'''_2 / dw_1 + 6 * dw'''_3 / dw_1
                  = ... = -5436
        dl / dw_2 = 4 * dw'''_1 / dw_2 + 5 * dw'''_2 / dw_2 + 6 * dw'''_3 / dw_2
                  = ... = -10875
        dl / dw_3 = 4 * dw'''_1 / dw_3 + 5 * dw'''_2 / dw_3 + 6 * dw'''_3 / dw_3
                  = ... = -16314
    """
    test_inputs = torch.tensor([[4., 5., 6.]])
    test_loss = model(test_inputs, params=params_3)
    grads = torch.autograd.grad(test_loss, model.parameters())

    assert test_loss.item() == -48939.
    assert len(grads) == 1
    assert torch.all(grads[0].data == torch.tensor([[-5436., -10875., -16314.]]))
