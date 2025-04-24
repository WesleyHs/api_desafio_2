from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import List
import models
from database import engine, get_db
from schemas import BancoApi
from datetime import datetime

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        if not file:
            raise HTTPException(status_code=400, detail="Nenhum arquivo localizado")
            
        content = (await file.read()).decode('utf-8').splitlines()
        
        results = {}
        
        for line in content:
            user_id = int(line[0:10].strip())
            name = line[10:55].strip()
            order_id = int(line[55:65].strip())
            product_id = int(line[65:75].strip())
            value = float(line[75:87].strip())
            date = line[-8:].strip()
            
            if user_id not in results:
                results[user_id] = {
                    'user_id': user_id,
                    'name': name,
                    'orders': {}
                }
            
            if order_id not in results[user_id]['orders']:
                results[user_id]['orders'][order_id] = {
                    'order_id': order_id,
                    'total': 0,
                    'date': datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d'),
                    'products': []
                }
            
            product = {
                'product_id': product_id,
                'value': f"{value:.2f}"
            }
            results[user_id]['orders'][order_id]['products'].append(product)
            results[user_id]['orders'][order_id]['total'] += value
        
        final_results = []
        for user_data in results.values():
            user_data['orders'] = list(user_data['orders'].values())
            for order in user_data['orders']:
                order['total'] = f"{order['total']:.2f}"
            final_results.append(user_data)
            
            data_all = db.query(models.BancoApi).filter(models.BancoApi.user_id == user_data['user_id']).first()
            if data_all:
                for key, value in user_data.items():
                    setattr(data_all, key, value)
            else:
                data_all = models.BancoApi(**user_data)
                db.add(data_all)
            
        db.commit()
        return final_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar arquivo: {str(e)}")

@app.get("/all/", response_model=List[BancoApi])
def get_all(db: Session = Depends(get_db)):
    return db.query(models.BancoApi).all()

@app.get("/order/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    try:
        data = db.query(models.BancoApi).all()
        
        results = {}
        for index in data:
            for order in index.orders:
                if order['order_id'] == order_id:
                    results = {
                        'user_id': index.user_id,
                        'name': index.name,
                        'orders': [order]
                    }
                    break
                    
        if not results:
            raise HTTPException(status_code=404, detail="Pedido não existe")
            
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail={"erro": str(e), "mensagem": "Erro ao processar"})

@app.get("/date/")
def get_by_date(
    start_date: str = Query(..., description="Data inicial no formato YYYYMMDD"),
    end_date: str = Query(..., description="Data final no formato YYYYMMDD"),
    db: Session = Depends(get_db)
):
    try:
        start_date = datetime.strptime(start_date, '%Y%m%d')
        end_date = datetime.strptime(end_date, '%Y%m%d')

        data = db.query(models.BancoApi).all()
        results = []

        for index in data:
            filtered_orders = []
            for order in index.orders:
                order_date = datetime.strptime(order['date'], '%Y-%m-%d')
                if start_date <= order_date <= end_date:
                    filtered_orders.append(order)
            
            if filtered_orders:
                results.append({
                    'user_id': index.user_id,
                    'name': index.name,
                    'orders': filtered_orders
                })

        if not results:
            raise HTTPException(status_code=404, detail="Não existe pedidos nesse periodo")

        return results

    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data invalido. Utilize YYYYMMDD")
    except Exception as e:
        raise HTTPException(status_code=500, detail={"erro": str(e), "mensagem": "Erro ao processar"}) 