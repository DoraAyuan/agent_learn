from app.skill_loader import load_all_skills


def main() -> None:
    skills = load_all_skills()

    print("=== 已加载的skills ===")

    for skill_name, skill_data in skills.items():
        print(f"\n--- {skill_name} ---")
        print(f"title: {skill_data['title']}")
        print("sections:")

        for section_name, section_content in skill_data["sections"].items():
            preview = section_content[:60].replace("\n", " ")
            print(f"  - {section_name}: {preview}")


if __name__ == "__main__":
    main()
