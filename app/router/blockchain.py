from fastapi import APIRouter, Depends
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
async def save_tokens():
    try:
        obj = Solscan()
        res = obj.save_tokens()
        return res
    except Exception as e:
        print(e)
        return {"success": False, "message": "Error occured while saving tokens."}