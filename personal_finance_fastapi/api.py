from fastapi import APIRouter,HTTPException
from schemas import RecordAdd
import crud

router=APIRouter()

@router.post('/add',summary='添加一条记账记录')
def add_record(record:RecordAdd):
    try:
        crud.create_record(
            amount=record.amount,
            category=record.category,
            remark=record.remark
        )
        return {'code':200,'msg':'记账成功','detail':record.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400,detail=f'记账失败:{str(e)}')
    
@router.get('/records',summary='按年月查询记录')
def get_records(year:int,month:int,page:int=1,page_size:int=5):
    try:
        if not(1<=month<=12):
            raise HTTPException(status_code=400,detail='月份范围必须为1-12')
        if page<1 or page_size<1:
            raise HTTPException(status_code=400,detail='页码/每页页数必须>=1')
        
        stats,records=crud.get_records_by_year_month(year,month,page,page_size)
        total_income=stats['total_income'] or 0.0
        total_expense=stats['total_expense'] or 0.0
        total_count=stats['total_count'] or 0.0
        total_balance=total_income-total_expense
        result=[]
        for r in records:
            result.append({
                "id":r['id'],
                'date':r['record_date'],
                'create_time':r['create_time'],
                'type':'收入' if r['amount']>0 else '支出',
                'amount':abs(r['amount']),
                'category':r['category'],
                'remark':r['remark']
            })
        return {
            'code':200,
            'msg':'查询成功',
            'data':{
                'pagination':{
                    'page':page,
                    'page_size':page_size,
                    'total_count':total_count,
                    'total_page':(total_count+page_size-1)//page_size#总页数
                },
                "statistics":{
                    "year":year,
                    "month":month,
                    "total_income":round(total_income,2),
                    "total_expense":round(total_expense,2),
                    "total_balance":round(total_balance,2)
                },
                'detail':result
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400,detail=f'查询失败:{str(e)}')
    
@router.delete('/delete/{record_idi}',summary='根据ID删除')
def delete_record(record_id:int,confirm:str=None):
        try:
            if not confirm or (confirm.lower() not in ['yes', 'y']):
                raise HTTPException(status_code=400,detail='已取消删除，删除需要输入yes or y')
            sucess=crud.delete_record(record_id)
            if not sucess:
                raise HTTPException(status_code=404,detail=f'ID{record_id}不存在')
            return {'code':200,'msg':f'ID{record_id}删除成功'}
        except HTTPException:
            raise#主动抛出错误，以免全部被下except Exception捕获
        except Exception as e:
            raise HTTPException(status_code=400,detail=f'删除失败{str(e)}')
        
@router.delete('/clear',summary='清空指定年月记账记录')
def clear_month(year:int,month:int,confirm:str=None):
    try:
        if not confirm or (confirm.lower() not in ['yes', 'y']):
            raise HTTPException(status_code=400,detail='已取消删除，删除需要输入yes or y')        
        if not(1<=month<=12):
            raise HTTPException(status_code=400,detail='月份范围必须为1-12')
        total=crud.clear_month_records(year,month)
        if total==0:
            raise HTTPException(status_code=400,detail=f'{year}年{month}月无记录可清空')
        return {'code':200,'msg':f'{year}年{month}月 记录已清空'}
    except HTTPException:
        raise#主动抛出错误，以免全部被下except Exception捕获
    except Exception as e:
        raise HTTPException(status_code=400,detail=f'清空失败：{str(e)}')
    

        

    