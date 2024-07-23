import json
import os
from leonardo_ai import LeonardoAI, LeonardoAIError


def main():
    api_key = "501cd296-31ae-4f7f-b50a-3736218826b7"  # TODO: HIDE API KEYS
    template_file = os.path.join(os.path.dirname(__file__), 'templates.json')
    leonardo = LeonardoAI(api_key=api_key, template_file=template_file)

    # Delete all generations
    try:
        for attempt in range(2000):
            # TODO: Document that this is dangerous as it deletes all images permanently
            leonardo.delete_all_generations()
            print("All generations have been successfully deleted.")
    except LeonardoAIError as e:
        print(f"Error deleting generations: {e}")


if __name__ == "__main__":
    main()
# TODO: do we need this?
