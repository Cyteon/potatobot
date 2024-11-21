import mongoose from "mongoose";

const economyUserSchema = new mongoose.Schema({
    id: String,
    balance: Number,
    lastDaily: Date
})

export default mongoose.model("EconomyUser", economyUserSchema, "economy_users");