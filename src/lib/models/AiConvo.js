import mongoose from "mongoose";

const aiConvosSchema = new mongoose.Schema({
  isChannel: Boolean,
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
  messageArray: [
    {
      role: String,
      content: String,
    },
  ],
  expiresAt: Number,
});

export default mongoose.model("ai_convo", aiConvosSchema, "ai_convos");
