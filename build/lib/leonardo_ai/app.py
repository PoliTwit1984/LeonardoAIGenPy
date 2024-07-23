import os
import time
from leonardo_ai import LeonardoAI, LeonardoAIError


def main():
    api_key = "501cd296-31ae-4f7f-b50a-3736218826b7"
    template_file = os.path.join(os.path.dirname(__file__), 'templates.json')
    leonardo = LeonardoAI(api_key=api_key, template_file=template_file)

    # Upload init image
    image_file_path = "pic.jpg"
    try:
        image_id = leonardo.upload_init_image(image_file_path)
        print(f"Uploaded image ID: {image_id}")
    except LeonardoAIError as e:
        print(f"Error uploading init image: {e}")
        return

    # Generate images using the uploaded init image and the 'artimage' template
    template_name = "artimage"
    try:
        if template_name in leonardo.templates:
            template = leonardo.templates[template_name]
            template["init_image_id"] = image_id
            template["init_strength"] = 0.2
            # Adding a proper prompt
            template["prompt"] = "An abstract oil painting of a beagle"

            # Logging the template details
            print(f"Template details: {template}")

            result = leonardo.generate_images(**template)
            print(f"Generated images: {result}")
        else:
            print(f"Template {template_name} not found.")
    except LeonardoAIError as e:
        print(f"Error generating images: {e}")
        return

    # Get the generated image ID
    try:
        generated_image_id = result["image_info"]["generated_images"][0]["id"]
        print(f"Generated image ID: {generated_image_id}")
    except KeyError as e:
        print(f"Error retrieving generated image ID: {e}")
        return

    # Create motion generation from the generated image
    try:
        motion_result = leonardo.create_motion_generation(
            image_id=generated_image_id, motion_strength=5)
        print(f"Motion generation result: {motion_result}")

        motion_job_id = motion_result["motionSvdGenerationJob"]["generationId"]
        print(f"Motion generation job ID: {motion_job_id}")

        # Waiting for the motion video generation to complete
        for i in range(9):
            print("Waiting for video generation...")
            time.sleep(10)

        # Retrieve the motion video URL
        motion_video_url = leonardo.get_motion_image_url_by_generation_id(
            motion_job_id)
        print(f"Motion video URL: {motion_video_url}")

    except LeonardoAIError as e:
        print(f"Error creating motion generation: {e}")
        return


if __name__ == "__main__":
    main()
