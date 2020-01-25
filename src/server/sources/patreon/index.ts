import {PatreonClient} from "./webdriver";

export class PatreonSource {
  private client: PatreonClient;

  constructor() {
    this.client = new PatreonClient();
  }

  public async run() {
    await this.client.login();
    await this.pollPosts();
    await this.client.close();
  }

  async pollPosts() {
    const result = await this.client.call("posts", {
      include: ["user"],
      fields: {
        post: [
          "title",
          "published_at",
          "current_user_can_view",
          "content",
          "image",
          "url",
        ],
        user: [
          "full_name",
          "image_url",
          "url",
        ],
      },
      sort: ["-published_at"],
      filter: {
        campaign_id: 88541,
        is_draft: false,
        contains_exclusive_posts: true,
      },
    });

    console.log("posts result", result);
  }
}
