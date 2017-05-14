# Using FB Face Recognition on Google Drive Pictures
How many times have you had to go through your albums to find pics of (or with) a specific friend? Do you remember those nights when you wanted to put together a quick collage before a friend's birthday but did not have the motivation to sort through your countless pics?

Same! I created this project to solve this real milleniial problem. Please note that running the script can take considerable amount of time for a large collection of pictures. However, you do not have to wait until all pics have been "classified." Interrupt the program (typically by **Ctrl + C**) whenever you wish.

## Setup
Following are the steps needed to run the app:
 - Turn on the Drive API by completing Step 1 [here](https://developers.google.com/drive/v3/web/quickstart/python). Your directory should have the `client_secret.json` file.
 - Install dependencies using 
    ```
    $ pip install -r requirements.txt
    ```
 - Create a Facebook config file `fb.json`
    - Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer) and generate an access token with `publish_actions`, `user_friends`, `user_photos`, and `user_posts` permissions.
    - Go to your Facebook profile
    - Press **F12** or right-click and choose **Inspect** to open Chrome Dev Tools
    - Head over to **Network** tab. Upload a picture and click on any `?dpr` endpoint in the **Network** tab (use filtering).
    - Scroll down to **Request Header** and copy the entire `cookie` string
    - Scroll down to **Form Data** and copy the `fb_dtsg` string
    - Your `fb.json` should be in the following format
      ```
      {
        "access_token": ACCESS_TOKEN,
        "cookie": COOKIE_STRING,
        "fb_dtsg": FB_DTSG_STRING
      }
      ```
  - Run app using
    ```
    $ python drive.py
    ```

## Thanks
A special shout-out to [samj1912](https://github.com/samj1912) for creating [fbrecog](https://github.com/samj1912/fbrecog) to provide a way to use Facebook's Face Recognition algorithm.

## Contributing
Please feel free to contact [Yash Mittal](yashmittal2009@gmail.com) or create a pull request. I am sure there's lots to improve.
