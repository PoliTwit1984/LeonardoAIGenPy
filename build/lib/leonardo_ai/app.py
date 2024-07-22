import json
import os
from leonardo_ai import LeonardoAI, LeonardoAIError


def main():
    api_key = "501cd296-31ae-4f7f-b50a-3736218826b7"
    template_file = os.path.join(os.path.dirname(__file__), 'templates.json')
    leonardo = LeonardoAI(api_key=api_key, template_file=template_file)

    # Specify the template name and prompt here
    template_name = "basicimage"  # Change this to the desired template
    prompt = "A beautiful brunette woman"  # Change this to the desired prompt

    if template_name in leonardo.templates:
        template = leonardo.templates[template_name]
        template["prompt"] = prompt

        try:
            result = leonardo.generate_images(**template)
            print(f"Generated images: {result}")
        except LeonardoAIError as e:
            print(
                f"Error generating images with template {template_name}: {e}")
    else:
        print(f"Template {template_name} not found.")


if __name__ == "__main__":
    main()
