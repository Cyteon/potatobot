import mongoose from "mongoose";

const globalUserSchema = new mongoose.Schema({
  id: {
    // TODO: Make this always string
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
});

export default mongoose.model("users_global", globalUserSchema, "users_global");
