import mongoose from "mongoose";

const guildsSchema = new mongoose.Schema({
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
  ticketChannel: String, // this only exists in this ver so can be properly typed
  ticketLogChannel: String, // same with this
  tickets_support_role: {
    // TODO: Make this always string
    type: BigInt,
    set: (val) => {
      return BigInt(val);
    },
    get: (val) => {
      return val.toString();
    },
  },
  log_channel: {
    // TODO: Make this always string
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
