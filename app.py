import io, base64
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("AGG")
import matplotlib.pyplot as plt
from matplotlib import font_manager

font_manager.fontManager.addfont("NanumGothic.ttf")
plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False

dist = pd.read_csv("district_summary.csv")
sh = pd.read_csv("shelters.csv")
hist = pd.read_csv("temp_hist.csv")
cen = sh.groupby("구")[["경도", "위도"]].mean()

def _z(x):
    r = x.max() - x.min()
    return (x - x.min()) / r if r else x * 0

def score(T, w_heat, w_pop, w_gap):
    h = hist[hist["기온"] >= T].groupby("구")["시간수"].sum()
    d = dist.copy()
    d["폭염시간"] = d["구"].map(h).fillna(0)
    s = w_heat + w_pop + w_gap
    d["취약도"] = (w_heat * _z(d["폭염시간"]) + w_pop * _z(d["고령60+"])
                + w_gap * (1 - _z(d["쉼터_고령1천명당"]))) / s * 100
    return d.sort_values("취약도", ascending=False).reset_index(drop=True)

def _fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

def make_plot(T, w_heat, w_pop, w_gap):
    d = score(T, w_heat, w_pop, w_gap)
    fig, ax = plt.subplots(2, 2, figsize=(15, 11))

    # 1) 쉼터 분포 + 구별 취약도 버블 (경계 데이터 없이 쉼터 좌표만 사용)
    a = ax[0, 0]
    a.scatter(sh["경도"], sh["위도"], s=3, c="#4c72b0", alpha=.35, label="무더위 쉼터")
    c = cen.loc[d["구"]]
    sc = a.scatter(c["경도"], c["위도"], s=d["고령60+"] / 120, c=d["취약도"],
                   cmap="YlOrRd", edgecolor="k", alpha=.8, vmin=0, vmax=100)
    for g, (x, y) in zip(d["구"], c.values):
        a.annotate(g, (x, y), ha="center", va="center", fontsize=8)
    a.set_aspect(1 / np.cos(np.radians(35.15)))
    a.set_title("쉼터 위치와 구별 취약도 (버블 크기=60세 이상 인구)")
    plt.colorbar(sc, ax=a, label="취약도")
    a.legend(loc="lower left")

    # 2) 취약도 순위
    a = ax[0, 1]
    top = d.iloc[::-1]
    a.barh(top["구"], top["취약도"], color=plt.cm.YlOrRd(top["취약도"] / 100))
    a.set_title(f"증설 우선순위 (폭염 기준 {T}℃ 이상)")
    a.set_xlabel("종합 취약도")

    # 3) 고령 1천명당 쉼터 vs 폭염 시간
    a = ax[1, 0]
    a.scatter(d["쉼터_고령1천명당"], d["폭염시간"], s=d["고령60+"] / 250,
              c=d["취약도"], cmap="YlOrRd", edgecolor="k", vmin=0, vmax=100)
    for _, r in d.iterrows():
        a.annotate(r["구"], (r["쉼터_고령1천명당"], r["폭염시간"]), fontsize=8,
                   xytext=(4, 4), textcoords="offset points")
    a.set_xlabel("60세 이상 1,000명당 쉼터 수")
    a.set_ylabel(f"{T}℃ 이상 시간 수 (6~9월)")
    a.set_title("위험(더위) 대비 공급: 오른쪽 아래가 안전, 왼쪽 위가 사각지대")

    # 4) 구 x 시간대 폭염 시간 히트맵
    a = ax[1, 1]
    p = (hist[hist["기온"] >= T].pivot_table(index="구", columns="시", values="시간수",
         aggfunc="sum").reindex(index=d["구"], columns=range(24)).fillna(0))
    im = a.imshow(p.values, aspect="auto", cmap="Reds")
    a.set_yticks(range(len(p))); a.set_yticklabels(p.index)
    a.set_xticks(range(0, 24, 2)); a.set_xticklabels(range(0, 24, 2))
    a.set_xlabel("시각"); a.set_title(f"{T}℃ 이상 발생 시간대 (취약도 순)")
    plt.colorbar(im, ax=a, label="시간 수")

    fig.tight_layout()
    return _fig_to_b64(fig)

def make_table(T, w_heat, w_pop, w_gap):
    d = score(T, w_heat, w_pop, w_gap)
    rows = "".join(
        f"<tr><td>{i+1}</td><td>{r['구']}</td><td>{r['취약도']:.1f}</td>"
        f"<td>{int(r['폭염시간'])}</td><td>{int(r['고령60+']):,}</td>"
        f"<td>{int(r['쉼터수'])}</td><td>{r['쉼터_고령1천명당']:.2f}</td></tr>"
        for i, r in d.iterrows())
    return ("<table><tr><th>순위</th><th>구</th><th>취약도</th><th>폭염시간</th>"
            "<th>60세+</th><th>쉼터</th><th>1천명당</th></tr>" + rows + "</table>")
