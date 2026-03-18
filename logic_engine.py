import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Position(BaseModel):
    symbol: str
    side: str
    entry_price: float
    size: float

class PortfolioRequest(BaseModel):
    action: str
    balance: float
    positions: List[Position]
    current_prices: Dict[str, float]

class SLTPRequest(BaseModel):
    action: str
    symbol: str
    side: str
    entry_price: float
    target_price: float
    lot_size: float

CONTRACT_SIZE = 100
LEVERAGE = 100

@app.post("/engine")
async def trading_engine(request: PortfolioRequest):
    if request.action == "calculate_portfolio":
        total_pnl = 0.0
        used_margin = 0.0
        
        for pos in request.positions:
            current_price = request.current_prices.get(pos.symbol, pos.entry_price)
            if pos.side == "BUY":
                diff = current_price - pos.entry_price
            else:
                diff = pos.entry_price - current_price
                
            pnl = diff * pos.size * CONTRACT_SIZE
            total_pnl += pnl
            margin = (pos.entry_price * pos.size * CONTRACT_SIZE) / LEVERAGE
            used_margin += margin
            
        equity = request.balance + total_pnl
        free_margin = equity - used_margin
        margin_level = (equity / used_margin) * 100 if used_margin > 0 else "---"

        return {
            "balance": request.balance,
            "equity": equity,
            "margin": used_margin,
            "free_margin": free_margin,
            "margin_level": round(margin_level, 2) if isinstance(margin_level, float) else margin_level,
            "total_floating_pnl": round(total_pnl, 2)
        }

@app.post("/project_sltp")
async def project_sl_tp(req: SLTPRequest):
    if req.side == "BUY":
        diff = req.target_price - req.entry_price
    else:
        diff = req.entry_price - req.target_price
    projected_pnl = diff * req.lot_size * CONTRACT_SIZE
    return {"projected_pnl": round(projected_pnl, 2)}
