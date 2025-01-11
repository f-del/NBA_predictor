import torch
DEFAULT_DEVICE = "cpu"
## Setup torch with Apple Silicon support or Cuda
def setup_torch_device(force_device: str =None):

    device = "cuda" if torch.cuda.is_available() else DEFAULT_DEVICE
    device = "mps" if torch.backends.mps.is_available() else DEFAULT_DEVICE

    # override for testing CPU vs MPS
    if force_device is not None:
        device = force_device

    torch.device(device)
    # Set torch as using the best available device (on Mac Silicon => mps)
    print(f"device: {device}", f"{torch.mps.device_count()} core" if device == "mps" else "")
    return device


torch.manual_seed(42)


def eval_model(model: torch.nn.Module,
               data_loader: torch.utils.data.DataLoader,
               loss_fn: torch.nn.Module,
               accuracy_fn,
               device: torch.device = DEFAULT_DEVICE):
    """Returns a dictionary containing the results of model predicting on data_loader.

    Args:
        model (torch.nn.Module): A PyTorch model capable of making predictions on data_loader.
        data_loader (torch.utils.data.DataLoader): The target dataset to predict on.
        loss_fn (torch.nn.Module): The loss function of model.
        accuracy_fn: An accuracy function to compare the models predictions to the truth labels.
        device: (torch.device) torch device to use, default DEFAULT_DEVICE.

    Returns:
        (dict): Results of model making predictions on data_loader.
    """
    loss, acc = 0, 0
    model.eval()
    with torch.inference_mode():
        for X, y in data_loader:
            # Make predictions with the model
            X, y = X.to(device), y.to(device)
            y_pred = model(X)

            # Accumulate the loss and accuracy values per batch
            loss += loss_fn(y_pred, y)
            acc += accuracy_fn(y.to(DEFAULT_DEVICE),
                               y_pred.to(DEFAULT_DEVICE).argmax(
                                   dim=1))  # For accuracy, need the prediction labels (logits -> pred_prob -> pred_labels)

        # Scale loss and acc to find the average loss/acc per batch
        loss /= len(data_loader)
        acc = acc / len(data_loader) * 100

    return {"name": model.__class__.__name__,
            "device": next(model.parameters()).device,# only works when model was created with a class
            "loss": loss.item(),
            "accuracy": float("{:.2f}".format(acc.item()))}




def train_step(model: torch.nn.Module,
               data_loader: torch.utils.data.DataLoader,
               loss_fn: torch.nn.Module,
               optimizer: torch.optim.Optimizer,
               accuracy_fn,
               device: torch.device = DEFAULT_DEVICE):
    train_loss, train_acc = 0, 0
    for batch, (X, y) in enumerate(data_loader):
        # Send data to GPU
        X, y = X.to(device), y.to(device)

        # 1. Forward pass
        y_pred = model(X)

        # 2. Calculate loss
        loss = loss_fn(y_pred, y)
        train_loss += loss
        train_acc += accuracy_fn(y.to(DEFAULT_DEVICE),
                                 y_pred.to(DEFAULT_DEVICE).argmax(dim=1))  # Go from logits -> pred labels

        # 3. Optimizer zero grad
        optimizer.zero_grad()

        # 4. Loss backward
        loss.backward()

        # 5. Optimizer step
        optimizer.step()

    # Calculate loss and accuracy per epoch and print out what's happening
    train_loss /= len(data_loader)
    train_acc = train_acc / len(data_loader) * 100
    print(f"Train loss: {train_loss:.5f} | Train accuracy: {train_acc:.2f}%")


def test_step(data_loader: torch.utils.data.DataLoader,
              model: torch.nn.Module,
              loss_fn: torch.nn.Module,
              accuracy_fn,
              device: torch.device = DEFAULT_DEVICE):
    test_loss, test_acc = 0, 0
    model.eval()  # put model in eval mode
    # Turn on inference context manager
    with torch.inference_mode():
        for X, y in data_loader:
            # Send data to GPU
            X, y = X.to(device), y.to(device)

            # 1. Forward pass
            y_pred = model(X)

            # 2. Calculate loss and accuracy
            test_loss += loss_fn(y_pred, y)
            test_acc += accuracy_fn(y.to(DEFAULT_DEVICE),
                                    y_pred.to(DEFAULT_DEVICE).argmax(dim=1)  # Go from logits -> pred labels
                                    )

        # Adjust metrics and print out
        test_loss /= len(data_loader)
        test_acc = test_acc / len(data_loader) * 100
        print(f"Test loss: {test_loss:.5f} | Test accuracy: {test_acc:.2f}%\n")