import mongoose from "mongoose";

const economyUserSchema = new mongoose.Schema({
  id: String,
  balance: {
    type: Number,
    default: 50,
  },
  lastDaily: Date,
  lastRobbed: Date,
});

export default mongoose.model(
  "EconomyUser",
  economyUserSchema,
  "economy_users",
);
