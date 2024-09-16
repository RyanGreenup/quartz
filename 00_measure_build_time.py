import os
import time
import subprocess
import shutil
import seaborn as sns
import polars as pl
import matplotlib.pyplot as plt


df = {
    "n": [],
    "time": [],
    "config": [],
    "hash": [],
}


# Assume File is in Quartz Directory
# os.chdir(os.path.basename(__file__))
top_dir = os.getcwd()
content_dir = "content"


def increase_file_count(n: int):
    original_dir = os.getcwd()
    os.chdir("./content")
    for i in range(n):
        shutil.copyfile("index.md", f"{i}_index.md")
    os.chdir(original_dir)


os.listdir("content/")
os.listdir(".")


def clear_file_count():
    # List the Files
    files = os.listdir(content_dir)
    # Remove everything
    [os.remove(os.path.join(content_dir, f)) for f in files]
    # Create an index file
    subprocess.run(
        ["npx", "quartz", "create", "-X", "new", "-l", "relative", "-s", "content/"]
    )


def set_file_num(n: int):
    files = os.listdir(content_dir)
    if len(files) > n:
        clear_file_count()
    increase_file_count(n)


def get_build_time():
    files = os.listdir(".")
    assert "quartz.config.ts" in files, "Must run this in Quartz Directory"

    start = time.time()
    subprocess.run(["npx", "quartz", "build"])
    end = time.time()

    return end - start


def get_git_hash() -> str:
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE, text=True
    )
    return out.stdout[:8]


def run_build(doc_counts: list[int], config: str):
    for i in doc_counts:
        set_file_num(i)
        t = get_build_time()

        df["n"].append(i)
        df["time"].append(t)
        df["config"].append(config)
        df["hash"].append(get_git_hash())

        print(pl.DataFrame(df))


# Repeat for last 4 commits
for i in range(4):
    # Number of Docs To Try
    num_docs = [10, 100, 200, 300, 500, 800, 1000, 1300, 1500, 2000]

    layout_file = "./quartz.layout.ts"
    layout_file_default = "./quartz.layout_default.ts"
    layout_file_no_explorer = "./quartz.layout_no_explorer.ts"

    # Use the Default Config
    shutil.copy(layout_file_default, layout_file)
    run_build(num_docs, "Default")

    # Use the Config without Explorer
    shutil.copy(layout_file_no_explorer, layout_file)
    run_build(num_docs, "No Explorer")

    # Save the Data
    pl.DataFrame(df).write_csv("Output_build_times.csv")

    # Plot the Times
    git_hash = get_git_hash()
    df_pl = pl.DataFrame(df)
    sns.scatterplot(df_pl, x="n", y="time", hue="config")
    plt.title(f"Build Time with and Without Explorer ({git_hash})")
    plt.xlabel("Number of Docs")
    plt.ylabel("Build Time (s)")
    plt.savefig(f"build_times_{git_hash}.png")
    # plt.show()

    # subprocess.run(["git", "stash"])
    subprocess.run(["git", "checkout", "HEAD^"])
    # subprocess.run(["git", "stash", "pop"])


# Plot all of the Data
df_pl = pl.read_csv("./Output_build_times.csv")
g = sns.FacetGrid(data=df_pl, col="hash", col_wrap=2, sharey=False, sharex=True)
g.map_dataframe(sns.scatterplot, x="n", hue="config", y="time")
g.add_legend()
g.set(xlabel="Number of Docs", ylabel="Build Time (s)")
g.figure.suptitle("Quartz Build Times")  # Add a main title to the plot
g.add_legend()
plt.savefig("build_times_all.png")
plt.show()
