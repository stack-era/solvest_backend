from fastapi import APIRouter, Depends, BackgroundTasks
from database import *
from app.solscan_api.solscan_api import Solscan
from .. import models

router = APIRouter()

def get_available_balances(key: str, db: Session):
    try:
        check = db.query(models.UsersKey).filter(models.UsersKey.publicKey == key).first()
        if not check:
            return {"success": False, "message": "Key does not exist in database, please add."}
        res = db.query(models.Balances).filter(models.BalancesKey.userId == check.id).all()
        return res
    except Exception as e:
        print(e)
        return {"succeed": False, "message": "Error occured while getting available balances"}

def update_balances(key: str, db: Session):
    try:
        check = db.query(models.UsersKey).filter(models.UsersKey.publicKey == key).first()
        if not check:
            return {"success": False, "message": "Key does not exist in database, please add."}
        obj = Solscan(key)
        res = obj.update_balances_in_db(check.id)
        return res
    except Exception as e:
        print(e)
        return {"success": False, "message": "Error occured while updating balances in database."}

def save_tokens_in_db():
    obj = Solscan()
    obj.save_tokens()

def fetch_solvest_tokens(db):
    try:
        res = db.query(models.SolvestTokens).with_entities(models.SolvestTokens.symbol.label("solvest_tkn_symbol"), models.SolvestTokens.name.label("solvest_tkn_name"), models.SolvestTokens.latestPrice.label("solvest_tkn_price"), models.UnderlyingTokens.symbol.label("under_tkn_symbol"), models.UnderlyingTokens.name.label("under_tkn_name"), models.UnderlyingTokens.weight.label("under_tkn_weight"))\
            .join(models.UnderlyingTokens, models.UnderlyingTokens.parentToken == models.SolvestTokens.id).all()
        response = dict()
        for row in res:
            if row.solvest_tkn_symbol not in response:
                response[row.solvest_tkn_symbol] = {"price": row.solvest_tkn_price, "name": row.solvest_tkn_name, "underlyingTokens": [{row.under_tkn_symbol: {"name": row.under_tkn_name, "weight": row.under_tkn_weight}}]}
            else:
                response[row.solvest_tkn_symbol]["underlyingTokens"].append({row.under_tkn_symbol: {"name": row.under_tkn_name, "weight": row.under_tkn_weight}})
        return response
    except Exception as e:
        print(e)
        return {"success": False, "message": "Error occured while fetching tokens."}

@router.get("/get_key_balances")
async def get_key_balances(key: str, db: Session = Depends(get_db)):
    res = get_available_balances(key, db)
    return res

@router.post("/update_balances_in_db")
async def update_balances_in_db(key: str, db: Session = Depends(get_db)):
    res = update_balances(key, db)
    return res

@router.get("/get_sol_balance")
async def get_sol_balance(key: str):
    try:
        obj = Solscan(key)
        res = obj.get_solana_balance()
        return res
    except Exception as e:
        print(e)
        return {"success": False, "message": "Error occured while getting solana balance."}

@router.get("/get_tokens")
async def get_tokens(limit: int, offset: int):
    try:
        obj = Solscan()
        res = obj.get_tokens(limit, offset)
        return res
    except Exception as e:
        print(e)
        return {"success": False, "message": "Error occured while getting tokens."}

@router.get("/save_tokens")
async def save_tokens(background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(save_tokens_in_db)
        res = {"success": True, "message": "Updating tokens in DB."}
        return res
    except Exception as e:
        print(e)
        return {"success": False, "message": "Error occured while saving tokens."}

@router.get("/get_solvest_tokens")
async def get_solvest_tokens(db: Session = Depends(get_db)):
    res = fetch_solvest_tokens(db)
    return res

@router.get("/get_token_transactions")
async def get_token_transactions(address: str, before: str = None):
    try:
        obj = Solscan()
        res = obj.get_token_transactions(address, before)
        return res
    except Exception as e:
        print(e)
        return {"success": False, "message": "Error occured while saving tokens"}