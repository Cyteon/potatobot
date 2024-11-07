import mongoose from "mongoose";

const guildsSchema = new mongoose.Schema({
  id: {
    type: BigInt,
    set: (val) => {
      return BigInt(val);
    },
    get: (val) => {
      return val.toString();
    },
  },
  ticketChannel: String, // this only exists in this ver so can be properly typed
  tickets_support_role: {
    type: BigInt,
    set: (val) => {
      return BigInt(val);
    },
    get: (val) => {
      return val.toString();
    },
  },
  ai_access: Boolean,
});

export default mongoose.model("Guild", guildsSchema);
