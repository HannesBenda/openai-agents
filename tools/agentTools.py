from agents import function_tool
import os
import git


@function_tool
def read_file_content(file_path: str) -> str:
    """
    Reads the content of a file.
    Args:
        file_path (str): The path to the file.
    Returns:
        str: The content of the file.
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        print(f"Read content from {file_path}")
        return content
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return f"Error: File not found at {file_path}"
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return f"Error reading file: {e}"

@function_tool
def get_current_working_directory() -> str:
    """
    Returns the current working directory as a string.
    """
    cwd = os.getcwd()
    return cwd+"/solutions.log"

@function_tool
def write_file_content(file_path: str, content: str) -> str:
    """
    Writes content to a file, overwriting existing content.
    Args:
        file_path (str): The path to the file.
        content (str): The content to write.
    Returns:
        str: A success message or an error message.
    """
    #print(f"file_path: {file_path}\ncontent: {content}")
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"---Content written to {file_path}")
        return f"Content successfully written to {file_path}"
    except Exception as e:
        print(f"Error writing to file {file_path}: {e}")
        return f"Error writing to file: {e}"

@function_tool
def create_directory(directory_path: str) -> str:
    """
    Creates a new directory if it does not already exist.
    Args:
        directory_path (str): The path of the directory to create.
    Returns:
        str: A success message or an error message.
    """
    try:
        # Use os.makedirs with exist_ok=True to avoid an error if the directory already exists
        os.makedirs(directory_path, exist_ok=True)
        print(f"---Directory created or already exists: {directory_path}")
        return f"Directory successfully created or already exists: {directory_path}"
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return f"Error creating directory: {e}"

@function_tool
def git_add(local_repo: str) -> str:
    """
    Stages and commits changes in a Git repository.
    Args:
        local_repo (str): The path to the Git repository.
    Returns:
        str: A success message or an error message.
    """
    try:
        repo = git.Repo(local_repo)
        repo.git.add(A=True) # Add all changed/untracked files
        print(f"Changes added in {local_repo}")
        return f"Changes added in {local_repo}"
    except git.GitCommandError as e:
        print(f"Error committing changes: {e}")
        return f"Error committing changes: {e}"
    except Exception as e:
        print(f"An unexpected error occurred during commit: {e}")
        return f"An unexpected error occurred during commit: {e}"
    
@function_tool
def list_files(local_repo: str, directory_path: str, index) -> str:
    """List files and directories in the given path."""
    if directory_path.startswith(f"repo_{index}/"):
        directory_path = directory_path[len(f"repo_{index}/"):]
    full_path = os.path.join(local_repo, directory_path)
    if not os.path.exists(full_path):
        return f"Error: Directory {directory_path} does not exist"
    try:
        items = []
        for item in sorted(os.listdir(full_path)):
            item_path = os.path.join(full_path, item)
            if os.path.isdir(item_path):
                items.append(f" {item}/")
            else:
                items.append(f" {item}")
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory {directory_path}: {str(e)}"
