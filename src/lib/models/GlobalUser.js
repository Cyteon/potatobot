import mongoose from "mongoose";
import { Long } from "mongodb";

const globalUserSchema = new mongoose.Schema({
  id: {
    type: BigInt,
    set: (val) => {
      return BigInt(val);
    },
    get: (val) => {
      return val.toString();
    },
  },
  blacklisted: Boolean,
  blacklist_reason: String,
  ai_ignore: Boolean,
  ai_ignore_reason: String,
  strikes: mongoose.Schema.Types.Mixed, // i dont fucking know
});

export default mongoose.model("users_global", globalUserSchema, "users_global");
