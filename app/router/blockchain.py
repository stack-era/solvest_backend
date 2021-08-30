from fastapi import APIRouter, Depends, BackgroundTasks
from database import *
from app.solscan_api.solscan_api import Solscan
from .. import models, schemas
from datetime import datetime
from sqlalchemy import DATE, cast

router = APIRouter()

def get_user_id(address: str, db: Session):
    try:
        res = db.query(models.UsersKey).with_entities(models.UsersKey.id).filter(models.UsersKey.publicKey == address).first()
        if not res:
            return None
        return res.id
    except Exception as e:
        print(e)
        return False

def get_available_balances(key: str, db: Session):
    try:
        check = db.query(models.UsersKey).filter(models.UsersKey.publicKey == key).first()
        if not check:
            return {"success": False, "message": "Key does not exist in database, please add."}
        res = db.query(models.Balances).filter(models.Balances.userId == check.id, models.Balances.priceUsdt != None).all()
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
    try:
        obj = Solscan()
        obj.save_tokens()
    except Exception as e:
        print(e)

def fetch_solvest_tokens(db):
    try:
        res = db.query(models.SolvestTokens).with_entities(models.SolvestTokens.id, models.SolvestTokens.symbol.label("solvest_tkn_symbol"), models.SolvestTokens.name.label("solvest_tkn_name"), models.SolvestTokens.latestPrice.label("solvest_tkn_price"), models.UnderlyingTokens.symbol.label("under_tkn_symbol"), models.UnderlyingTokens.name.label("under_tkn_name"), models.UnderlyingTokens.weight.label("under_tkn_weight"))\
            .join(models.UnderlyingTokens, models.UnderlyingTokens.parentToken == models.SolvestTokens.id).all()
        response = dict()
        for row in res:
            if row.solvest_tkn_symbol not in response:
                response[row.solvest_tkn_symbol] = {"id": row.id, "price": row.solvest_tkn_price, "name": row.solvest_tkn_name, "underlyingTokens": [{row.under_tkn_symbol: {"name": row.under_tkn_name, "weight": row.under_tkn_weight}}]}
            else:
                response[row.solvest_tkn_symbol]["underlyingTokens"].append({row.under_tkn_symbol: {"name": row.under_tkn_name, "weight": row.under_tkn_weight}})
        return response
    except Exception as e:
        print(e)
        return {"success": False, "message": "Error occured while fetching tokens."}

def save_user_stream(streamData: schemas.StreamCreate, db: Session):
    try:
        user_id = get_user_id(streamData.publicAddress, db)
        if user_id is None:
            return {"success": False, "message": "User Key not found."}
        elif user_id == False:
            return {"success": False, "message": "Error occured while creating stream."}
        insertStream = models.UserStreams(userId=user_id, solvestToken=streamData.solvesToken, startTimestamp=datetime.utcnow(), interval=streamData.interval, active=True)
        db.add(insertStream)
        db.commit()
        return {"success": True, "message": "Added stream successfully"}
    except Exception as e:
        print(e)
        return {"success": False, "message": "Error occured while adding stream."}

def fetch_key_streams(key: str, db: Session):
    try:
        res = db.query(models.UserStreams).join(models.UsersKey, models.UsersKey.id == models.UserStreams.id).filter(models.UsersKey.publicKey == key).all()
        return res
    except Exception as e:
        print(e)
        return {"status": False, "message": "Error occured while getting streams."}

def stop_user_stream(streamId: int, db: Session):
    try:
        updateData = {"active": False, "stopTimestamp": datetime.utcnow()}
        db.query(models.UserStreams).filter(models.UserStreams.id == streamId).update(updateData, synchronize_session=False)
        db.commit()
        return {"success": True, "message": "Stream updated successfully"}
    except Exception as e:
        print(e)
        return {"success": False, "message": "Error occured while updating stream."}

def get_user_historical_portfolio(publicKey: str, db: Session):
    try:
        userId = get_user_id(publicKey, db)
        if userId is None:
            return {"success": False, "message": "User Key not found."}
        elif userId == False:
            return {"success": False, "message": "Error occured while creating stream."}
        res = db.query(models.UserHistoricalPortfolio).with_entities((cast(models.UserHistoricalPortfolio.timestamp, DATE)).label('date'), models.UserHistoricalPortfolio.balance, models.SolanaTokens.symbol, models.TokensDailyData.closePrice)\
                .join(models.SolanaTokens, models.SolanaTokens.address == models.UserHistoricalPortfolio.tokenAddress)\
                .join(models.TokensDailyData, (models.TokensDailyData.tokenAddress == models.UserHistoricalPortfolio.tokenAddress) & (cast(models.UserHistoricalPortfolio.timestamp, DATE) == models.TokensDailyData.date))\
                .order_by(models.UserHistoricalPortfolio.timestamp.desc()).filter(models.UserHistoricalPortfolio.userId == userId).all()
        portfolio_dic = dict()
        for row in res:
            if row['date'] not in portfolio_dic:
                portfolio_dic[row['date']] = float(row.balance * row.closePrice)
            else:
                portfolio_dic[row['date']] += float(row.balance * row.closePrice)
        response = {"success": True, "data": portfolio_dic}
        return response
    except Exception as e:
        print(e)
        return {"success": False, "message": "Error occured while getting historical portfolio."}

########################################################################################################
########################################################################################################

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

@router.post("/save_stream")
async def save_stream(streamData: schemas.StreamCreate, db: Session = Depends(get_db)):
    res = save_user_stream(streamData, db)
    return res

@router.get("/get_streams")
async def get_streams(publicKey: str, db: Session = Depends(get_db)):
    res = fetch_key_streams(publicKey, db)
    return res

@router.get("/stop_stream")
async def stop_stream(streamId: int, db: Session = Depends(get_db)):
    res = stop_user_stream(streamId, db)
    return res

@router.get("/user_historical_portfolio")
async def user_historical_portfolio(publicKey: str, db: Session = Depends(get_db)):
    res = get_user_historical_portfolio(publicKey, db)
    return res