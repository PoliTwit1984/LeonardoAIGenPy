import requests
from typing import Dict, List, Any
import os
import time
import json


class LeonardoAIError(Exception):
    """Custom exception class for LeonardoAI errors"""
    pass


class LeonardoAI:
    def __init__(self, api_key: str, template_file: str = None):
        """
        Initialize the LeonardoAI client with the provided API key.
        :param api_key: Your Leonardo AI API key
        :param template_file: Path to the template file (default: None)
        """
        self.api_key = api_key
        if not self.api_key:
            raise LeonardoAIError("API key must be provided.")
        self.base_url = "https://cloud.leonardo.ai/api/rest/v1"
        self.headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.api_key}",
            "content-type": "application/json"
        }
        self.user_id = self.get_user_id()
        if template_file:
            self.templates = self.load_templates(template_file)
        else:
            self.templates = {}

    def get_user_id(self) -> str:
        """
        Retrieve the user ID using the provided API key.
        :return: User ID
        """
        try:
            response = self._make_request("GET", "me")
            return response['user_details'][0]['user']['id']
        except Exception as e:
            raise LeonardoAIError(f"Error retrieving user ID: {e}")

    # ... other methods ...
    def load_templates(self, template_file: str) -> dict:
        """
        Load templates from a JSON file.
        :param template_file: Path to the template file
        :return: Dictionary of templates
        """
        try:
            with open(template_file, 'r') as file:
                templates = json.load(file)
                return templates
        except Exception as e:
            print(f"Error loading templates: {e}")
            return {}

    # TODO: Add type hints for method and endpoint
    def _make_request(self, method: str, endpoint: str, params: Dict = {}, payload: Dict = {}) -> Dict:
        """
        Make a request to the Leonardo AI API.
        :param method: HTTP method (GET, POST, etc.)
        :param endpoint: API endpoint
        :param params: Query parameters for GET requests
        :param payload: Request payload for POST requests
        :return: JSON response from the API
        """
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(
            method, url, headers=self.headers, params=params, json=payload)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise LeonardoAIError("Unauthorized: Check your API key.")
        elif response.status_code == 404:
            raise LeonardoAIError(
                f"Not Found: The endpoint {endpoint} was not found.")
        else:
            raise LeonardoAIError(
                f"API request failed with status {response.status_code}: {response.text}")

    def _poll_job_completion(self, job_id: str, endpoint: str, poll_interval: int = 10, timeout: int = 300) -> Dict:
        """
        Poll the job completion status.
        :param job_id: The ID of the job.
        :param endpoint: The API endpoint to check the job status.
        :param poll_interval: Time in seconds between status checks (default: 10).
        :param timeout: Maximum time in seconds to wait for completion (default: 300).
        :return: JSON response containing job status information.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                url = f"{self.base_url}/{endpoint}/{job_id}"
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    job_status = response.json()
                    if 'generated_image_variation_generic' in job_status:
                        if job_status['generated_image_variation_generic'][0]['status'] == 'COMPLETE':
                            return job_status
                        elif job_status['generated_image_variation_generic'][0]['status'] == 'FAILED':
                            raise LeonardoAIError("Job failed.")
                else:
                    raise LeonardoAIError(
                        f"API request failed with status {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Error retrieving job status: {e}")

            time.sleep(poll_interval)

        raise LeonardoAIError(
            f"Job {job_id} did not complete within {timeout} seconds")

    def get_single_generation(self, generation_id: str) -> Dict:
        """
        Retrieve information about a specific generation.
        :param generation_id: The ID of the generation to retrieve
        :return: Dictionary containing information about the generation
        """
        try:
            response = self._make_request(
                "GET", f"generations/{generation_id}")
            # Debugging line
            print(f"API response for generation {generation_id}: {response}")

            generated_images = response.get(
                'generations_by_pk', {}).get('generated_images', [])
            if not generated_images:
                raise LeonardoAIError(
                    f"Generation with ID {generation_id} not found in the response")

            return response['generations_by_pk']
        except LeonardoAIError as e:
            print(f"Error in get_single_generation: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error in get_single_generation: {e}")
            raise

    def generate_images(self,
                        prompt: str,
                        model_id: str = None,
                        num_images: int = 1,
                        width: int = 1024,
                        height: int = 1024,
                        alchemy: bool = True,
                        photoReal: bool = True,
                        photoRealVersion: str = "v2",
                        presetStyle: str = "DYNAMIC",
                        wait_for_completion: bool = True,
                        guidance_scale: int = 7,
                        contrastRatio: float = None,
                        controlnets: List[Dict] = None,
                        elements: List[Dict] = None,
                        expandedDomain: bool = False,
                        fantasyAvatar: bool = False,
                        highContrast: bool = False,
                        highResolution: bool = False,
                        imagePrompts: List[str] = None,
                        imagePromptWeight: float = None,
                        init_generation_image_id: str = None,
                        init_image_id: str = None,
                        init_strength: float = None,
                        negative_prompt: str = None,
                        num_inference_steps: int = 15,
                        photoRealStrength: float = None,
                        promptMagic: bool = False,
                        promptMagicStrength: float = None,
                        promptMagicVersion: str = None,
                        public: bool = None,
                        scheduler: str = None,
                        sd_version: str = None,
                        seed: int = None,
                        tiling: bool = None,
                        transparency: str = None,
                        unzoom: bool = None,
                        unzoomAmount: float = None,
                        upscaleRatio: float = None,
                        template_name: str = None) -> Dict:
        """
        Generate images based on a text prompt.
        :param prompt: Text description of the image to generate
        :param model_id: ID of the AI model to use
        :param num_images: Number of images to generate (default: 1, max: 4 if width or height > 768)
        :param width: Width of the generated image(s) (default: 1024)
        :param height: Height of the generated image(s) (default: 1024)
        :param alchemy: Enable to use Alchemy (default: True)
        :param photoReal: Enable to use photoReal feature (default: True)
        :param photoRealVersion: Version of photoReal to use ("v1" or "v2", default: "v2")
        :param presetStyle: Style preset for the generation (default: "DYNAMIC")
        :param wait_for_completion: If True, wait for the generation to complete (default: True)
        :param guidance_scale: How strongly the generation should reflect the prompt (default: 7)
        :param contrastRatio: Contrast Ratio to use with Alchemy (float between 0 and 1 inclusive)
        :param controlnets: List of controlnet objects or None
        :param elements: List of element objects or None
        :param expandedDomain: Enable to use the Expanded Domain feature of Alchemy (default: False)
        :param fantasyAvatar: Enable to use the Fantasy Avatar feature (default: False)
        :param highContrast: Enable to use the High Contrast feature of Prompt Magic (default: False)
        :param highResolution: Enable to use the High Resolution feature of Prompt Magic (default: False)
        :param imagePrompts: List of image prompt URLs or None
        :param imagePromptWeight: Weight of the image prompt (float)
        :param init_generation_image_id: ID of an existing image to use in image2image
        :param init_image_id: ID of an Init Image to use in image2image
        :param init_strength: How strongly the generated images should reflect the original image in image2image (float between 0.1 and 0.9)
        :param negative_prompt: Negative prompt used for the image generation
        :param num_inference_steps: Step count to use for the generation (default: 15, range: 10-60)
        :param photoRealStrength: Depth of field for photoReal (0.55 for low, 0.5 for medium, 0.45 for high)
        :param promptMagic: Enable to use Prompt Magic (default: False)
        :param promptMagicStrength: Strength of Prompt Magic (float between 0.1 and 1.0)
        :param promptMagicVersion: Version of Prompt Magic to use ("v2" or "v3") when promptMagic is enabled
        :param public: Whether the generated images should show in the community feed (default: None)
        :param scheduler: Scheduler to generate images with (default: "EULER_DISCRETE")
        :param sd_version: Base version of stable diffusion to use if not using a custom model (e.g., "v1_5", "v2", "SDXL")
        :param seed: Seed for the generation to ensure reproducibility (default: None)
        :param tiling: Whether the generated images should tile on all axes (default: None)
        :param transparency: Type of transparency the image should use (default: None)
        :param unzoom: Whether the generated images should be unzoomed (requires unzoomAmount and init_image_id)
        :param unzoomAmount: How much the image should be unzoomed (requires unzoom and init_image_id)
        :param upscaleRatio: How much the image should be upscaled (Enterprise Only, default: None)
        :param template_name: Name of the template to use for generation (default: None)
        :return: Dictionary containing generation ID and image URLs (if waited for completion)
        """
        photoreal_v2_models = {
            "Leonardo Kino XL": "aa77f04e-3eec-4034-9c07-d0f619684628",
            "Leonardo Diffusion XL": "1e60896f-3c26-4296-8ecc-53e2afecc132",
            "Leonardo Vision XL": "5c232a9e-9061-4777-980a-ddc8e65647c6"
        }

        if template_name and template_name in self.templates:
            template = self.templates[template_name]
            prompt = template.get("prompt", prompt)
            model_id = template.get("model_id", model_id)
            num_images = template.get("num_images", num_images)
            width = template.get("width", width)
            height = template.get("height", height)
            alchemy = template.get("alchemy", alchemy)
            photoReal = template.get("photoReal", photoReal)
            photoRealVersion = template.get(
                "photoRealVersion", photoRealVersion)
            presetStyle = template.get("presetStyle", presetStyle)
            guidance_scale = template.get("guidance_scale", guidance_scale)
            num_inference_steps = template.get(
                "num_inference_steps", num_inference_steps)
            init_image_id = template.get("init_image_id", init_image_id)
            init_strength = template.get("init_strength", init_strength)

        if photoRealVersion == "v2":
            if model_id not in photoreal_v2_models.values():
                raise LeonardoAIError(
                    "PhotoReal v2 requires a model id specified as either Leonardo Kino XL, Leonardo Diffusion XL, or Leonardo Vision XL.")
            alchemy = True

        payload = {
            "prompt": prompt,
            "modelId": model_id,
            "num_images": num_images,
            "width": width,
            "height": height,
            "alchemy": alchemy,
            "photoReal": photoReal,
            "photoRealVersion": photoRealVersion,
            "presetStyle": presetStyle,
            "guidance_scale": guidance_scale,
            "contrastRatio": contrastRatio,
            "controlnets": controlnets,
            "elements": elements,
            "expandedDomain": expandedDomain,
            "fantasyAvatar": fantasyAvatar,
            "highContrast": highContrast,
            "highResolution": highResolution,
            "imagePrompts": imagePrompts,
            "imagePromptWeight": imagePromptWeight,
            "init_generation_image_id": init_generation_image_id,
            "init_image_id": init_image_id,
            "init_strength": init_strength,
            "negative_prompt": negative_prompt,
            "num_inference_steps": num_inference_steps,
            "photoRealStrength": photoRealStrength,
            "promptMagic": promptMagic,
            "promptMagicStrength": promptMagicStrength,
            "promptMagicVersion": promptMagicVersion,
            "public": public,
            "scheduler": scheduler,
            "sd_version": sd_version,
            "seed": seed,
            "tiling": tiling,
            "transparency": transparency,
            "unzoom": unzoom,
            "unzoomAmount": unzoomAmount,
            "upscaleRatio": upscaleRatio,
        }

        generation_data = self._make_request(
            "POST", "generations", payload=payload)
        generation_id = generation_data.get(
            'sdGenerationJob', {}).get('generationId')

        if not generation_id:
            raise LeonardoAIError("Failed to start image generation")

        result = {"generation_id": generation_id}

        if wait_for_completion:
            print(f"Waiting for generation {generation_id} to complete...")
            images_info = self.wait_for_generation_completion(generation_id)
            result["image_info"] = images_info

        return result

    def wait_for_generation_completion(self, generation_id: str, poll_interval: int = 10, timeout: int = 300) -> List[Dict[str, Any]]:
        """
        Wait for the generation to complete and return the generated images.
        :param generation_id: The ID of the generation to wait for
        :param poll_interval: Time in seconds between status checks (default: 10)
        :param timeout: Maximum time in seconds to wait for completion (default: 300)
        :return: List of dictionaries containing generated image information
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                generation_info = self.get_single_generation(generation_id)
                if generation_info:
                    return generation_info
            except LeonardoAIError as e:
                print(f"Waiting for generation completion: {e}")
            time.sleep(poll_interval)
        raise LeonardoAIError(
            f"Generation {generation_id} did not complete within {timeout} seconds")

    def download_images(self, image_urls: List[Dict[str, Any]], save_dir: str):
        """
        Download images from a list of image URLs and save them to the specified directory.
        :param image_urls: List of dictionaries containing image URL and metadata
        :param save_dir: Directory to save the downloaded images
        """
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        for image_info in image_urls:
            image_url = image_info['url']
            image_id = image_info['id']
            image_path = os.path.join(save_dir, f"{image_id}.jpg")

            response = requests.get(image_url)
            if response.status_code == 200:
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded image {image_id} to {image_path}")
            else:
                print(f"Failed to download image {image_id} from {image_url}")

    def download_images_from_generation(self, generation_id: str, save_dir: str):
        """
        Wait for a generation to complete and download all generated images.
        :param generation_id: The ID of the generation to wait for and download images from
        :param save_dir: Directory to save the downloaded images
        """
        images_info = self.wait_for_generation_completion(generation_id)
        self.download_images(images_info, save_dir)

    def improve_prompt(self, prompt: str) -> Dict:
        """
        Improve a given text prompt.

        This method sends a POST request to the Leonardo AI API to improve the provided prompt.

        :param prompt: The prompt to improve
        :return: Dictionary containing the improved prompt

        Example:
        >>> leonardo = LeonardoAI(api_key="your_api_key_here")
        >>> improved_prompt_data = leonardo.improve_prompt("beautiful woman in lingerie")
        >>> print(improved_prompt_data["prompt"])
        """
        payload = {"prompt": prompt}
        improved_prompt_data = self._make_request(
            "POST", "prompt/improve", payload=payload)
        return improved_prompt_data.get("promptGeneration", {})

    def get_user_info(self) -> Dict:
        """
        Retrieve information about the authenticated user.

        This method sends a GET request to the Leonardo AI API to retrieve the user's information such as user ID, username, token renewal date, and current amounts of subscription tokens, GPT tokens, and model training tokens.

        :return: Dictionary containing user information

        Example:
        >>> leonardo = LeonardoAI(api_key="your_api_key_here")
        >>> user_info = leonardo.get_user_info()
        >>> print(user_info)
        """
        return self._make_request("GET", "me")

    def list_image_ids_from_generation(self, generation_id: str) -> List[str]:
        """
        List all image IDs from a specific generation.

        :param generation_id: The ID of the generation to retrieve image IDs from.
        :return: List of image IDs.
        """
        try:
            generation_info = self.get_single_generation(generation_id)
            return [image['id'] for image in generation_info]
        except Exception as e:
            print(f"Error listing image IDs from generation: {e}")
            return []

    def upscale_image(self, generated_image_id: str) -> Dict:
        """
        Upscale an image using the Universal Upscaler.

        :param generated_image_id: The ID of the generated image to upscale.
        :return: Dictionary containing the result of the upscaling operation.
        """
        url = f"{self.base_url}/variations/upscale"
        payload = {
            "id": generated_image_id
        }
        print(f"Upscale request payload: {payload}")  # Log the payload
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            print(f"Upscale response: {response.json()}")  # Log the response
            return response.json()
        else:
            raise LeonardoAIError(
                f"API request failed with status {response.status_code}: {response.text}")

    def get_upscaled_image(self, upscale_job_id: str, poll_interval: int = 10, timeout: int = 300) -> str:
        """
        Retrieve the URL of the upscaled image.

        :param upscale_job_id: The ID of the upscale job.
        :param poll_interval: Time in seconds between status checks (default: 10).
        :param timeout: Maximum time in seconds to wait for completion (default: 300).
        :return: URL of the upscaled image.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                url = f"{self.base_url}/variations/{upscale_job_id}"
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    job_status = response.json()
                    print(f"Job status: {job_status}")
                    if 'generated_image_variation_generic' in job_status:
                        for item in job_status['generated_image_variation_generic']:
                            if item['status'] == 'COMPLETE' and item['url']:
                                return item['url']
                            elif item['status'] == 'FAILED':
                                raise LeonardoAIError("Upscaling job failed.")
                else:
                    raise LeonardoAIError(
                        f"API request failed with status {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Error retrieving upscaled image: {e}")

            time.sleep(poll_interval)

        raise LeonardoAIError(
            f"Upscaling job {upscale_job_id} did not complete within {timeout} seconds")

    def create_motion_generation(self, image_id: str, is_public: bool = False, is_init_image: bool = False, is_variation: bool = False, motion_strength: int = None) -> Dict:
        """
        Create a motion generation for the specified image.

        :param image_id: The ID of the image to create motion for.
        :param is_public: Whether the generation is public or not (default: False).
        :param is_init_image: If it is an init image uploaded by the user (default: False).
        :param is_variation: If it is a variation image (default: False).
        :param motion_strength: The motion strength.
        :return: Dictionary containing the result of the motion generation.
        """
        payload = {
            "imageId": image_id,
            "isPublic": is_public,
            "isInitImage": is_init_image,
            "isVariation": is_variation,
            "motionStrength": motion_strength,
        }

        response = requests.post(
            f"{self.base_url}/generations-motion-svd", headers=self.headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise LeonardoAIError(
                f"API request failed with status {response.status_code}: {response.text}"
            )

    def get_template(self, template_name: str, templates: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get a specific template by name.
        :param template_name: The name of the template to retrieve
        :param templates: Dictionary of loaded templates
        :return: Template data as a dictionary
        """
        return templates.get(template_name, {})

    def generate_image_from_template(self, prompt: str, template_name: str):
        """
        Generate an image using a template.
        :param prompt: The text prompt for the image generation
        :param template_name: The name of the template to use
        :return: Dictionary containing generation ID and image URLs (if waited for completion)
        """
        template = self.get_template(template_name, self.templates)
        if template:
            template['prompt'] = prompt
            return self.generate_images(**template)
        else:
            raise LeonardoAIError(f"Template {template_name} not found.")

    def create_universal_upscaler(self, generated_image_id: str, poll_interval: int = 10, timeout: int = 300) -> Dict:
        """
        Create a high-resolution image using the Universal Upscaler.

        :param generated_image_id: The ID of the generated image to upscale.
        :param poll_interval: Time in seconds between status checks (default: 10).
        :param timeout: Maximum time in seconds to wait for completion (default: 300).
        :return: Dictionary containing the result of the upscaling operation.
        """
        url = f"{self.base_url}/variations/universal-upscaler"
        payload = {
            "upscalerStyle": "CINEMATIC",
            "creativityStrength": 5,
            "upscaleMultiplier": 1.5,
            "generatedImageId": generated_image_id
        }
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            upscaler_job_id = response.json().get("universalUpscaler", {}).get("id")
            if not upscaler_job_id:
                raise LeonardoAIError("Failed to retrieve upscaler job ID")

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    job_status = self._make_request(
                        "GET", f"variations/{upscaler_job_id}")
                    print(f"Job status: {job_status}")  # Debugging line
                    if 'generated_image_variation_generic' in job_status and job_status['generated_image_variation_generic'][0]['status'] == 'COMPLETE':
                        return job_status['generated_image_variation_generic'][0]
                    elif job_status['generated_image_variation_generic'][0]['status'] == 'FAILED':
                        raise LeonardoAIError("Upscaling job failed.")
                except Exception as e:
                    print(f"Error retrieving upscaled image: {e}")

                time.sleep(poll_interval)

            raise LeonardoAIError(
                f"Upscaling job {upscaler_job_id} did not complete within {timeout} seconds")
        else:
            raise LeonardoAIError(
                f"API request failed with status {response.status_code}: {response.text}")

    def get_generations_by_user_id(self) -> List[Dict]:
        """
        Retrieve all generations by the user.
        :return: List of dictionaries containing generation information
        """
        try:
            response = self._make_request(
                "GET", f"generations/user/{self.user_id}")
            return response.get('generations', [])
        except Exception as e:
            print(f"Error retrieving generations by user ID: {e}")
            return []

    def delete_generation_by_id(self, generation_id: str) -> None:
        """
        Delete a specific generation by its ID.
        :param generation_id: The ID of the generation to delete
        """
        try:
            self._make_request("DELETE", f"generations/{generation_id}")
            print(f"Successfully deleted generation ID: {generation_id}")
        except Exception as e:
            print(f"Error deleting generation ID {generation_id}: {e}")

    def delete_all_generations(self) -> None:
        """
        Delete all generations by the user.
        """
        generations = self.get_generations_by_user_id()
        for generation in generations:
            generation_id = generation['id']
            self.delete_generation_by_id(generation_id)

    def create_unzoom(self, image_id: str, is_variation: bool = False) -> Dict:
        """
        Create an unzoom variation for the provided image ID.

        :param image_id: The ID of the image to unzoom.
        :param is_variation: Whether the image is a variation (default: False).
        :return: Dictionary containing the result of the unzoom operation.
        """
        url = f"{self.base_url}/variations/unzoom"
        payload = {
            "id": image_id,
            "isVariation": is_variation
        }
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise LeonardoAIError(
                f"API request failed with status {response.status_code}: {response.text}"
            )

    def upload_init_image(self, image_file_path: str, extension: str = "jpg") -> str:
        """
        Upload an init image and return the image ID.

        :param image_file_path: Path to the image file.
        :param extension: File extension (default: "jpg").
        :return: Image ID of the uploaded image.
        """
        payload = {"extension": extension}
        response = self._make_request("POST", "init-image", payload=payload)

        fields_str = response['uploadInitImage']['fields']
        fields = json.loads(fields_str)
        url = response['uploadInitImage']['url']
        image_id = response['uploadInitImage']['id']

        with open(image_file_path, 'rb') as image_file:
            files = {'file': image_file}
            upload_response = requests.post(url, data=fields, files=files)

        if upload_response.status_code != 204:
            raise LeonardoAIError("Failed to upload the image")

        return image_id

    def get_motion_image_url_by_generation_id(self, generation_id: str) -> str:
        """
        Retrieve the URL of the motion generation image by generation ID.

        :param generation_id: The ID of the motion generation.
        :return: URL of the motion image.
        """
        try:
            url = f"{self.base_url}/generations/{generation_id}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                job_status = response.json()
                if 'generations_by_pk' in job_status:
                    for item in job_status['generations_by_pk']['generated_images']:
                        if item['motionMP4URL']:
                            return item['motionMP4URL']
                else:
                    raise LeonardoAIError(
                        "Motion generation job not completed or failed.")
            else:
                raise LeonardoAIError(
                    f"API request failed with status {response.status_code}: {response.text}")
        except Exception as e:
            raise LeonardoAIError(f"Error retrieving motion image: {e}")
