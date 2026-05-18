from app.skill_loader import load_all_skills
from app.skill_selector import select_skill


def main() -> None:
    skills = load_all_skills()

    query = "帮我总结一篇关于深度学习在医学影像中的论文"

    result = select_skill(query, skills)

    print("\n=== 选择结果 ===")
    print(result)


if __name__ == "__main__":
    main()
