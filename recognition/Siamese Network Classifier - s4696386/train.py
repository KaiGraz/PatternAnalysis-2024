import torch, argparse

from modules import SiameseNetwork
from dataset import APP_MATCHER

# With support from:
# https://github.com/pytorch/examples/blob/main/siamese_network

def train(model: SiameseNetwork, device, train_loader, optimizer, epoch, log_interval, dry_run):
    model.train()
    
    criterion = model.loss_criterion

    for batch_idx, (images_1, images_2, targets) in enumerate(train_loader):
        images_1, images_2, targets = images_1.to(device), images_2.to(device), targets.to(device)
        optimizer.zero_grad()
        outputs = model(images_1, images_2).squeeze()
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        if batch_idx % log_interval == 0:
            print(f"Train Epoch: {epoch} [{batch_idx*len(images_1)}/{len(train_loader.dataset)} ({100. * batch_idx / len(train_loader)}%)]")
            print(f"Loss: {loss.item()}")
            if dry_run:
                break

def test(model: SiameseNetwork, device, test_loader):
    model.eval()
    test_loss = 0
    correct = 0

    criterion = model.loss_criterion

    with torch.no_grad():
        for (images_1, images_2, targets) in test_loader:
            images_1, images_2, targets = images_1.to(device), images_2.to(device), targets.to(device)
            outputs = model(images_1, images_2).squeeze()
            test_loss += criterion(outputs, targets).sum().item()  # sum up batch loss
            pred = torch.where(outputs > 0.5, 1, 0)  # get the index of the max log-probability
            correct += pred.eq(targets.view_as(pred)).sum().item()

    test_loss /= len(test_loader.dataset)

    print(f'Test set: Average loss: {test_loss}, Accuracy: {correct}/{len(test_loader.dataset)} ({100. * correct / len(test_loader.dataset)}%)\n')

def main():
    torch_seed = 10
    batch_size = 16
    shuffle = True
    gamma = 0.7
    epochs = 10
    learning_rate = 1.0
    save_model = False
    log_interval = 10
    dry_run = True
    

    torch.manual_seed(torch_seed)

    # Use cuda device if available
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

    # Create Datasets and place them into DataLoaders
    train_dataset = APP_MATCHER(image_folder="E:/COMP3710 Project/ISIC_2020_Train_DICOM_corrected", ground_truth_file="E:/COMP3710 Project/ISIC_2020_Training_GroundTruth.csv", train=True)
    test_dataset = APP_MATCHER(image_folder="E:/COMP3710 Project/ISIC_2020_Train_DICOM_corrected", ground_truth_file="E:/COMP3710 Project/ISIC_2020_Training_GroundTruth.csv",train=False)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size, shuffle)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size, shuffle)

    # Create the model
    model = SiameseNetwork().to(device)
    # Define which optimizer to use
    optimizer = torch.optim.Adadelta(model.parameters(), lr=learning_rate)
    # Create scheduler
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=gamma)
    
    # run epochs
    for epoch in range(1, epochs+1):
        train(model, device, train_loader, optimizer, epoch, log_interval, dry_run)
        test(model, device, test_loader)
        scheduler.step()

    if save_model:
        torch.save(model.state_dict(), "siamese_network.pt")

# Only run main when running file directly (not during imports)
if __name__ == "__main__":
    import cProfile, pstats, os

    current_directory = os.getcwd()
    with cProfile.Profile() as pr:
        main()
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    os.chdir(current_directory)
    stats.dump_stats(filename="profile.prof")