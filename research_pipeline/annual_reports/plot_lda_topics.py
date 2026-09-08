from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PUBLIC_DATA = Path(__file__).with_name("lda_topic_plot_data_en.csv")
DEFAULT_OUT = REPO_ROOT / "assets" / "research" / "annual_report_lda_topics_en.png"

TRANSLATIONS = {
    "AI": "AI",
    "ML": "ML",
    "DL": "DL",
    "IoT": "IoT",
    "B2B": "B2B",
    "B2C": "B2C",
    "O2O": "O2O",
    "\u7269\u8054\u7f51": "Internet of Things",
    "\u4eba\u5de5\u667a\u80fd": "Artificial intelligence",
    "\u901a\u4fe1": "Communications",
    "\u82af\u7247": "Chips",
    "\u5de5\u4e1a\u4e92\u8054\u7f51": "Industrial internet",
    "\u667a\u80fd\u5236\u9020": "Smart manufacturing",
    "\u7b97\u6cd5": "Algorithms",
    "\u5927\u6570\u636e": "Big data",
    "\u8f6f\u4ef6": "Software",
    "\u5b89\u5168": "Security",
    "\u4e91\u8ba1\u7b97": "Cloud computing",
    "\u667a\u6167\u57ce\u5e02": "Smart cities",
    "\u8d4b\u80fd": "Digital enablement",
    "\u7535\u5546": "E-commerce",
    "\u7535\u5b50\u5546\u52a1": "Electronic commerce",
    "\u91d1\u878d\u79d1\u6280": "FinTech",
    "\u7f51\u7edc": "Network",
    "\u6570\u5b57\u5316": "Digitalization",
    "\u6570\u5b57\u5316\u8f6c\u578b": "Digital transformation",
    "\u667a\u80fd\u673a\u5668\u4eba": "Intelligent robotics",
    "\u9ad8\u8d28\u91cf": "High quality",
}

TOPIC_LABELS = {
    0: "AI, IoT, and Smart Manufacturing",
    1: "Data, Software, and Cloud Systems",
    2: "E-Commerce and FinTech",
    3: "Digital Transformation and Automation",
}

TOPIC_SPACE_LABELS = {
    0: "AI / IoT",
    1: "Data / Cloud",
    2: "E-Commerce",
    3: "Digitalization",
}


def _topic_word_matrix(model, topn: int = 6) -> tuple[pd.DataFrame, np.ndarray]:
    rows = []
    topic_vectors = model.get_topics()
    for topic_id in range(model.num_topics):
        for keyword, weight in model.show_topic(topic_id, topn=topn):
            rows.append(
                {
                    "topic_id": topic_id,
                    "topic_label": TOPIC_LABELS.get(topic_id, f"Topic {topic_id}"),
                    "keyword": TRANSLATIONS.get(keyword, keyword),
                    "original_rank": len([row for row in rows if row["topic_id"] == topic_id]) + 1,
                    "word_weight": float(weight),
                }
            )
    return pd.DataFrame(rows), topic_vectors


def _pca_coordinates(matrix: np.ndarray) -> np.ndarray:
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    coords = centered @ vt[:2].T
    return coords


def build_public_plot_data(lda_out_dir: Path, output_csv: Path) -> pd.DataFrame:
    from gensim import models

    model_path = lda_out_dir / "lda_model_sampled_t4.gz"
    bubble_path = lda_out_dir / "topic_bubbles.csv"
    if not model_path.exists():
        raise FileNotFoundError(f"Missing LDA model: {model_path}")
    if not bubble_path.exists():
        raise FileNotFoundError(f"Missing topic prevalence data: {bubble_path}")

    model = models.LdaModel.load(str(model_path))
    keyword_df, topic_vectors = _topic_word_matrix(model, topn=6)
    coords = _pca_coordinates(topic_vectors)
    prevalence = (
        pd.read_csv(bubble_path)
        .groupby("topic_id", as_index=False)["avg_prob"]
        .mean()
        .rename(columns={"avg_prob": "prevalence"})
    )
    coord_df = pd.DataFrame(
        {
            "topic_id": list(range(model.num_topics)),
            "x": coords[:, 0],
            "y": coords[:, 1],
        }
    )
    topic_df = keyword_df.merge(prevalence, on="topic_id", how="left").merge(coord_df, on="topic_id", how="left")
    topic_df.to_csv(output_csv, index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)
    return topic_df


def load_plot_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing plot data: {path}")
    return pd.read_csv(path)


def plot_lda_topics(data: pd.DataFrame, output_path: Path) -> None:
    topics = (
        data[["topic_id", "topic_label", "prevalence", "x", "y"]]
        .drop_duplicates()
        .sort_values("topic_id")
        .reset_index(drop=True)
    )
    colors = ["#2d6f8f", "#5f8f3a", "#bd6b2f", "#6d5b9a"]

    fig = plt.figure(figsize=(16, 8.8), dpi=320)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1.25], wspace=0.18)
    ax_space = fig.add_subplot(gs[0, 0])
    ax_words = fig.add_subplot(gs[0, 1])

    fig.suptitle("LDA Topic Structure in A-Share Annual Reports", fontsize=22, fontweight="bold", y=0.975)
    fig.text(
        0.5,
        0.936,
        "Traditional topic modeling for exploratory text measurement; separate from the LLM extraction pipeline",
        ha="center",
        va="center",
        fontsize=12.5,
        color="#4d5966",
    )

    sizes = 2200 * topics["prevalence"] / topics["prevalence"].max()
    ax_space.scatter(
        topics["x"],
        topics["y"],
        s=sizes,
        c=colors[: len(topics)],
        alpha=0.78,
        edgecolors="#1f2937",
        linewidths=1.2,
    )
    for i, row in topics.iterrows():
        label = f"Topic {int(row.topic_id)}\n{TOPIC_SPACE_LABELS.get(int(row.topic_id), row.topic_label)}"
        ax_space.annotate(
            label,
            (row.x, row.y),
            xytext=(8, 8),
            textcoords="offset points",
            fontsize=9.8,
            color="#17212b",
            bbox={"boxstyle": "round,pad=0.28", "fc": "white", "ec": "#d8dee6", "alpha": 0.92},
        )
    ax_space.axhline(0, color="#d8dee6", linewidth=0.9, zorder=0)
    ax_space.axvline(0, color="#d8dee6", linewidth=0.9, zorder=0)
    ax_space.set_title("A. Topic Space and Relative Prevalence", loc="left", fontsize=14, fontweight="bold", pad=14)
    ax_space.set_xlabel("PCA component 1 from topic-word probabilities")
    ax_space.set_ylabel("PCA component 2 from topic-word probabilities")
    x_pad = (topics["x"].max() - topics["x"].min()) * 0.2
    y_pad = (topics["y"].max() - topics["y"].min()) * 0.18
    ax_space.set_xlim(topics["x"].min() - x_pad, topics["x"].max() + x_pad)
    ax_space.set_ylim(topics["y"].min() - y_pad, topics["y"].max() + y_pad)
    ax_space.grid(True, color="#edf0f2", linewidth=0.8)
    ax_space.spines[["top", "right"]].set_visible(False)

    ax_words.set_title("B. Representative Topic Keywords", loc="left", fontsize=14, fontweight="bold", pad=14)
    ax_words.axis("off")
    selected_topics = topics["topic_id"].astype(int).tolist()[:4]
    card_height = 0.215
    top_start = 0.92
    for order, topic_id in enumerate(selected_topics):
        topic_rows = data[data["topic_id"] == topic_id].sort_values("original_rank").head(6)
        y0 = top_start - order * 0.235
        color = colors[order % len(colors)]
        ax_words.add_patch(
            plt.Rectangle((0.015, y0 - card_height), 0.96, card_height, transform=ax_words.transAxes, fc="white", ec="#d8dee6", lw=1.0)
        )
        topic_label = topic_rows["topic_label"].iloc[0]
        prevalence = topic_rows["prevalence"].iloc[0]
        ax_words.text(
            0.04,
            y0 - 0.035,
            f"Topic {topic_id}: {topic_label}",
            transform=ax_words.transAxes,
            fontsize=11.5,
            fontweight="bold",
            color="#17212b",
            va="center",
        )
        ax_words.text(
            0.78,
            y0 - 0.035,
            f"mean prevalence {prevalence:.3f}",
            transform=ax_words.transAxes,
            fontsize=9.5,
            color="#526170",
            va="center",
        )
        max_weight = topic_rows["word_weight"].max()
        for i, item in enumerate(topic_rows.itertuples(index=False)):
            y = y0 - 0.078 - i * 0.023
            width = 0.33 * item.word_weight / max_weight
            ax_words.text(0.055, y, item.keyword, transform=ax_words.transAxes, fontsize=9.5, color="#26333f", va="center")
            ax_words.add_patch(
                plt.Rectangle((0.42, y - 0.008), width, 0.014, transform=ax_words.transAxes, fc=color, ec="none", alpha=0.82)
            )
            ax_words.text(0.42 + width + 0.012, y, f"{item.word_weight:.3f}", transform=ax_words.transAxes, fontsize=8.5, color="#526170", va="center")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=320, bbox_inches="tight", facecolor="white", pil_kwargs={"dpi": (320, 320)})
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot the English annual-report LDA topic visualization.")
    parser.add_argument("--lda-out-dir", type=Path, help="Optional path to private LDA/out outputs for rebuilding plot data.")
    parser.add_argument("--data", type=Path, default=DEFAULT_PUBLIC_DATA, help="Public derived plot-data CSV.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT, help="Output PNG path.")
    args = parser.parse_args()

    if args.lda_out_dir:
        data = build_public_plot_data(args.lda_out_dir, args.data)
    else:
        data = load_plot_data(args.data)
    plot_lda_topics(data, args.output)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
