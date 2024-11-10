import mongoose from "mongoose";

const aiChannelsSchema = new mongoose.Schema({
  ai_channels: [String],
});

export default mongoose.model("ai_channels", aiChannelsSchema, "ai_channels");
