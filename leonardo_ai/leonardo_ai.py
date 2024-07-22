import requests
from typing import Dict, List, Any
import os
import time
import json


class LeonardoAIError(Exception):
    """Custom exception class for LeonardoAI errors"""
    pass


class LeonardoAI:
    def __init__(self, api_key: str, template_file: str = "templates.json"):
        """
        Initialize the LeonardoAI client with the provided API key.
        :param api_key: Your Leonardo AI API key
        :param template_file: Path to the template file (default: "templates.json")
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
        self.templates = self.load_templates(template_file)

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
            generated_images = response.get(
                'generations_by_pk', {}).get('generated_images', [])
            if not generated_images:
                raise LeonardoAIError(
                    f"Generation with ID {generation_id} not found in the response")
            return generated_images
        except LeonardoAIError as e:
            print(f"Error in get_single_generation: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error in get_single_generation: {e}")
            raise

    def get_models(self) -> List[Dict]:
        """
        Get a list of available AI models.
        :return: List of dictionaries containing model information
        """
        try:
            data = self._make_request("GET", "platformModels")
            print("API response data:", data)  # Debugging line
            if isinstance(data, dict) and 'models' in data:
                return [{'id': model['id'], 'name': model['name'], 'description': model['description']}
                        for model in data['models']]
            else:
                raise LeonardoAIError("Unexpected response structure")
        except Exception as e:
            print(f"Error retrieving models: {e}")
            return []

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
                        upscaleRatio: float = None) -> Dict:
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
        :return: Dictionary containing generation ID and image URLs (if waited for completion)
        """
        photoreal_v2_models = {
            "Leonardo Kino XL": "aa77f04e-3eec-4034-9c07-d0f619684628",
            "Leonardo Diffusion XL": "1e60896f-3c26-4296-8ecc-53e2afecc132",
            "Leonardo Vision XL": "5c232a9e-9061-4777-980a-ddc8e65647c6"
        }

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
        job_status = self._poll_job_completion(
            upscale_job_id, "variations", poll_interval, timeout)
        return job_status['generated_image_variation_generic'][0]['url']

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

    def get_motion_image_url(self, motion_job_id: str, poll_interval: int = 10, timeout: int = 300) -> str:
        """
        Retrieve the URL of the motion generation image.

        :param motion_job_id: The ID of the motion job.
        :param poll_interval: Time in seconds between status checks (default: 10).
        :param timeout: Maximum time in seconds to wait for completion (default: 300).
        :return: URL of the motion image.
        """
        job_status = self._poll_job_completion(
            motion_job_id, "generations-motion-svd", poll_interval, timeout)
        return job_status['generated_image_variation_generic'][0]['motionMP4URL']

    def get_motion_image(self, motion_job_id: str, poll_interval: int = 10, timeout: int = 300) -> str:
        """
        Retrieve the URL of the motion generation image.

        :param motion_job_id: The ID of the motion job.
        :param poll_interval: Time in seconds between status checks (default: 10).
        :param timeout: Maximum time in seconds to wait for completion (default: 300).
        :return: URL of the motion image.
        """
        job_status = self._poll_job_completion(
            motion_job_id, "generations-motion-svd", poll_interval, timeout)
        return job_status['generated_image_variation_generic'][0]['motionMP4URL']

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
