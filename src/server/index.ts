import * as dotenv from "dotenv";
dotenv.config();

import {PatreonSource} from "./sources/patreon";

const patreon = new PatreonSource();
patreon.run().catch((error) => {
  console.error(error);
});
